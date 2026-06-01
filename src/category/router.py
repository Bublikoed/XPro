from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.category.schemas import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListItem
from src.category.service import CategoryService

router = APIRouter(prefix="/category", tags=["Категорії (Category)"])


@router.get("", response_model=List[CategoryListItem])
async def get_categories(
    search_id: Optional[int] = Query(None, description="Пошук за ID"),
    search_name: Optional[str] = Query(
        None, description="Пошук за назвою (сегмент або повний шлях категорії)"
    ),
    status_filter: Optional[str] = Query(None, description="Фільтрація за статусом ('1' або '0')"),
    sort_by_name: Optional[str] = Query(None, description="Сортування за алфавітом структури ('asc' або 'desc')"),
    sort_by_id: Optional[str] = Query(None, description="Сортування за ID ('asc' або 'desc')"),
    page: int = Query(1, ge=1, description="Номер сторінки (пагінація)"),
    limit: int = Query(20, ge=1, le=100, description="Кількість елементів на сторінці"),
    db: AsyncSession = Depends(get_db),
):
    return await CategoryService.async_get_all_categories(
        db=db,
        search_id=search_id,
        search_name=search_name,
        status_filter=status_filter,
        sort_by_name_direction=sort_by_name,
        sort_by_id_direction=sort_by_id,
        page=page,
        limit=limit,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await CategoryService.async_get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з ID {category_id} не знайдено",
        )
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category_data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await CategoryService.async_create_category(db, category_data)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int, update_data: CategoryUpdate, db: AsyncSession = Depends(get_db)
):
    updated_category = await CategoryService.async_update_category(db, category_id, update_data)
    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з ID {category_id} не знайдено",
        )
    return updated_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    success = await CategoryService.async_delete_category(db, category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з ID {category_id} не знайдено",
        )
    return
