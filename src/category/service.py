from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.category.models import Category
from src.category.schemas import CategoryCreate, CategoryListItem, CategoryUpdate
from src.common.status_labels import category_status_label


class CategoryService:

    @staticmethod
    def _build_full_path(category: Category, all_categories_dict: dict[int, Category]) -> str:
        if (
            category.parent_category_id
            and category.parent_category_id != 0
            and category.parent_category_id in all_categories_dict
        ):
            parent = all_categories_dict[category.parent_category_id]
            return f"{CategoryService._build_full_path(parent, all_categories_dict)} > {category.name}"
        return category.name

    @staticmethod
    async def _load_all_categories_dict(db: AsyncSession) -> dict[int, Category]:
        result = await db.execute(select(Category))
        return {cat.category_id: cat for cat in result.scalars().all()}

    @staticmethod
    async def _attach_full_path(db: AsyncSession, category: Category) -> None:
        all_dict = await CategoryService._load_all_categories_dict(db)
        category.full_path = CategoryService._build_full_path(category, all_dict)

    @staticmethod
    def _to_list_item(category: Category) -> CategoryListItem:
        return CategoryListItem(
            category_id=category.category_id,
            name=category.full_path or category.name,
            status=category_status_label(category.status),
        )

    @staticmethod
    def _sort_tree_preorder(
        categories: List[Category],
        all_categories_dict: dict[int, Category],
    ) -> List[Category]:
        """Обхід дерева: батько → діти; серед братів — за category_id (як у прикладі ТЗ)."""
        by_id = {cat.category_id: cat for cat in categories}
        ids_in_result = set(by_id.keys())

        children_by_parent: dict[int, list[int]] = {}
        for cat in all_categories_dict.values():
            parent_id = cat.parent_category_id or 0
            if parent_id != 0 and parent_id not in all_categories_dict:
                parent_id = 0
            children_by_parent.setdefault(parent_id, []).append(cat.category_id)

        for sibling_ids in children_by_parent.values():
            sibling_ids.sort()

        ordered: List[Category] = []
        visited: set[int] = set()

        def visit(parent_id: int) -> None:
            for cid in children_by_parent.get(parent_id, []):
                if cid in ids_in_result and cid not in visited:
                    ordered.append(by_id[cid])
                    visited.add(cid)
                visit(cid)

        visit(0)

        for cat in sorted(categories, key=lambda c: c.category_id):
            if cat.category_id not in visited:
                ordered.append(cat)

        return ordered

    @staticmethod
    def _matches_name_search(category: Category, search_name: str) -> bool:
        needle = search_name.casefold()
        full_path = (category.full_path or category.name).casefold()
        if needle in full_path:
            return True
        return needle in category.name.casefold()

    @staticmethod
    async def async_get_all_categories(
        db: AsyncSession,
        search_id: Optional[int] = None,
        search_name: Optional[str] = None,
        status_filter: Optional[str] = None,
        sort_by_name_direction: Optional[str] = None,
        sort_by_id_direction: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> List[CategoryListItem]:
        query = select(Category)

        if search_id is not None:
            query = query.where(Category.category_id == search_id)
        if status_filter is not None:
            query = query.where(Category.status == status_filter)

        result = await db.execute(query)
        categories_list = list(result.scalars().all())

        all_categories_dict = await CategoryService._load_all_categories_dict(db)
        for cat in categories_list:
            cat.full_path = CategoryService._build_full_path(cat, all_categories_dict)

        if search_name is not None:
            categories_list = [
                cat
                for cat in categories_list
                if CategoryService._matches_name_search(cat, search_name)
            ]

        if sort_by_name_direction == "asc":
            categories_list.sort(key=lambda x: x.full_path)
        elif sort_by_name_direction == "desc":
            categories_list.sort(key=lambda x: x.full_path, reverse=True)
        elif sort_by_id_direction == "asc":
            categories_list.sort(key=lambda x: x.category_id)
        elif sort_by_id_direction == "desc":
            categories_list.sort(key=lambda x: x.category_id, reverse=True)
        else:
            categories_list = CategoryService._sort_tree_preorder(
                categories_list, all_categories_dict
            )

        start_index = (page - 1) * limit
        end_index = start_index + limit
        page_items = categories_list[start_index:end_index]
        return [CategoryService._to_list_item(cat) for cat in page_items]

    @staticmethod
    async def async_get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
        query = select(Category).where(Category.category_id == category_id)
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        if category:
            await CategoryService._attach_full_path(db, category)
        return category

    @staticmethod
    async def async_create_category(db: AsyncSession, category_data: CategoryCreate) -> Category:
        new_category = Category(**category_data.model_dump())
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        await CategoryService._attach_full_path(db, new_category)
        return new_category

    @staticmethod
    async def async_update_category(
        db: AsyncSession, category_id: int, update_data: CategoryUpdate
    ) -> Optional[Category]:
        category = await CategoryService.async_get_category_by_id(db, category_id)
        if not category:
            return None

        data_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in data_dict.items():
            setattr(category, key, value)

        await db.commit()
        await db.refresh(category)
        await CategoryService._attach_full_path(db, category)
        return category

    @staticmethod
    def _collect_descendant_ids(category_id: int, all_categories: list[Category]) -> set[int]:
        ids_to_delete = {category_id}
        changed = True
        while changed:
            changed = False
            for cat in all_categories:
                if cat.parent_category_id in ids_to_delete and cat.category_id not in ids_to_delete:
                    ids_to_delete.add(cat.category_id)
                    changed = True
        return ids_to_delete

    @staticmethod
    async def async_delete_category(db: AsyncSession, category_id: int) -> bool:
        category = await CategoryService.async_get_category_by_id(db, category_id)
        if not category:
            return False

        result = await db.execute(select(Category))
        all_categories = list(result.scalars().all())
        ids_to_delete = CategoryService._collect_descendant_ids(category_id, all_categories)

        for cat in all_categories:
            if cat.category_id in ids_to_delete:
                db.delete(cat)

        await db.commit()
        return True
