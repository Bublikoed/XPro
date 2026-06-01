from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.category.models import Category
from src.category.service import CategoryService
from src.common.status_labels import product_status_label
from src.product.models import (
    Product,
    ProductImage,
    ProductAttribute,
    ProductCategory,
    ProductStore,
    Manufacturer,
    Store,
)
from src.product.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductListItem,
    ProductResponse,
    ProductImageResponse,
    ProductImageUpdate,
    ProductAttributeResponse,
    ProductAttributeUpdate,
    ProductCategoryLinkResponse,
    ProductStoreResponse,
    ManufacturerResponse,
)
from src.category.schemas import CategoryResponse


class ProductService:

    @staticmethod
    def _primary_category_path(product: Product, all_categories_dict: dict[int, Category]) -> str:
        if not product.categories:
            return ""
        paths = [
            CategoryService._build_full_path(cat, all_categories_dict)
            for cat in product.categories
        ]
        return min(paths)

    @staticmethod
    async def _build_product_response(
        db: AsyncSession,
        product: Product,
        *,
        increment_view: bool = False,
    ) -> ProductResponse:
        if increment_view:
            product.viewed += 1
            await db.commit()
            await db.refresh(product)

        all_cat_dict = await CategoryService._load_all_categories_dict(db)

        categories_resp: List[CategoryResponse] = []
        for cat in product.categories:
            cat.full_path = CategoryService._build_full_path(cat, all_cat_dict)
            categories_resp.append(CategoryResponse.model_validate(cat))

        stores_resp = [
            ProductStoreResponse(
                product_store_id=link.product_store_id,
                product_id=link.product_id,
                store_id=link.store_id,
                store_name=link.store.name,
            )
            for link in product.product_stores
        ]

        manufacturer_resp = None
        if product.manufacturer:
            manufacturer_resp = ManufacturerResponse.model_validate(product.manufacturer)

        return ProductResponse(
            product_id=product.product_id,
            name=product.name,
            description=product.description,
            seo_keyword=product.seo_keyword,
            meta_title=product.meta_title,
            meta_description=product.meta_description,
            meta_keyword=product.meta_keyword,
            image=product.image,
            price=product.price,
            model=product.model or "",
            manufacturer_id=product.manufacturer_id,
            status=product.status,
            status_label=product_status_label(product.status),
            rating=product.rating,
            viewed=product.viewed,
            date_added=product.date_added,
            date_modify=product.date_modify,
            manufacturer=manufacturer_resp,
            categories=categories_resp,
            images=[ProductImageResponse.model_validate(img) for img in product.images],
            attributes=[ProductAttributeResponse.model_validate(a) for a in product.attributes],
            stores=stores_resp,
        )

    @staticmethod
    async def _get_product_orm(
        db: AsyncSession, product_id: int
    ) -> Optional[Product]:
        query = (
            select(Product)
            .where(Product.product_id == product_id)
            .options(
                selectinload(Product.categories),
                selectinload(Product.images),
                selectinload(Product.attributes),
                selectinload(Product.manufacturer),
                selectinload(Product.product_stores).selectinload(ProductStore.store),
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def async_get_all_products(
        db: AsyncSession,
        category_id: Optional[int] = None,
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        sort_by_name_direction: Optional[str] = None,
        sort_by_price_direction: Optional[str] = None,
        sort_by_category_direction: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> List[ProductListItem]:
        query = select(Product).options(
            selectinload(Product.categories),
        )

        if price_from is not None:
            query = query.where(Product.price >= price_from)
        if price_to is not None:
            query = query.where(Product.price <= price_to)
        if category_id is not None:
            query = query.join(ProductCategory).where(ProductCategory.category_id == category_id)

        result = await db.execute(query)
        products_list = list(result.scalars().unique().all())
        all_categories_dict = await CategoryService._load_all_categories_dict(db)

        if sort_by_name_direction == "asc":
            products_list.sort(key=lambda x: x.name)
        elif sort_by_name_direction == "desc":
            products_list.sort(key=lambda x: x.name, reverse=True)
        elif sort_by_price_direction == "asc":
            products_list.sort(key=lambda x: x.price)
        elif sort_by_price_direction == "desc":
            products_list.sort(key=lambda x: x.price, reverse=True)
        elif sort_by_category_direction == "asc":
            products_list.sort(
                key=lambda p: ProductService._primary_category_path(p, all_categories_dict)
            )
        elif sort_by_category_direction == "desc":
            products_list.sort(
                key=lambda p: ProductService._primary_category_path(p, all_categories_dict),
                reverse=True,
            )

        start_index = (page - 1) * limit
        page_products = products_list[start_index : start_index + limit]

        items: List[ProductListItem] = []
        for prod in page_products:
            items.append(
                ProductListItem(
                    product_id=prod.product_id,
                    name=prod.name,
                    category=ProductService._primary_category_path(
                        prod, all_categories_dict
                    ),
                    price=prod.price,
                )
            )
        return items

    @staticmethod
    async def async_get_product_by_id(
        db: AsyncSession, product_id: int, *, increment_view: bool = True
    ) -> Optional[ProductResponse]:
        product = await ProductService._get_product_orm(db, product_id)
        if not product:
            return None
        return await ProductService._build_product_response(
            db, product, increment_view=increment_view
        )

    @staticmethod
    async def async_create_product(db: AsyncSession, product_data: ProductCreate) -> ProductResponse:
        payload = product_data.model_dump(
            exclude={"category_ids", "store_ids", "images", "attributes"}
        )
        if payload.get("manufacturer_id") == 0:
            payload["manufacturer_id"] = None

        new_product = Product(**payload)
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)

        for cat_id in product_data.category_ids:
            db.add(ProductCategory(product_id=new_product.product_id, category_id=cat_id))
        for store_id in product_data.store_ids:
            db.add(ProductStore(product_id=new_product.product_id, store_id=store_id))
        for img in product_data.images:
            db.add(ProductImage(product_id=new_product.product_id, **img.model_dump()))
        for attr in product_data.attributes:
            db.add(ProductAttribute(product_id=new_product.product_id, **attr.model_dump()))

        await db.commit()
        result = await ProductService.async_get_product_by_id(
            db, new_product.product_id, increment_view=False
        )
        assert result is not None
        return result

    @staticmethod
    async def async_update_product(
        db: AsyncSession, product_id: int, update_data: ProductUpdate
    ) -> Optional[ProductResponse]:
        product = await ProductService._get_product_orm(db, product_id)
        if not product:
            return None

        data_dict = update_data.model_dump(exclude_unset=True)
        if data_dict.get("manufacturer_id") == 0:
            data_dict["manufacturer_id"] = None
        for key, value in data_dict.items():
            setattr(product, key, value)

        await db.commit()
        return await ProductService.async_get_product_by_id(db, product_id, increment_view=False)

    @staticmethod
    async def async_delete_product(db: AsyncSession, product_id: int) -> bool:
        product = await ProductService._get_product_orm(db, product_id)
        if not product:
            return False
        db.delete(product)
        await db.commit()
        return True

    @staticmethod
    async def _ensure_product_exists(db: AsyncSession, product_id: int) -> bool:
        result = await db.execute(select(Product.product_id).where(Product.product_id == product_id))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def build_category_link_response(
        db: AsyncSession, link: ProductCategory
    ) -> ProductCategoryLinkResponse:
        all_dict = await CategoryService._load_all_categories_dict(db)
        cat = all_dict.get(link.category_id)
        path = CategoryService._build_full_path(cat, all_dict) if cat else ""
        return ProductCategoryLinkResponse(
            product_category_id=link.product_category_id,
            product_id=link.product_id,
            category_id=link.category_id,
            category_name=path,
        )
