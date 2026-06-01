from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.product.models import (
    ProductImage,
    ProductAttribute,
    ProductCategory,
    ProductStore,
)
from src.product.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListItem,
    ProductImageResponse,
    ProductImageCreate,
    ProductImageUpdate,
    ProductAttributeResponse,
    ProductAttributeCreate,
    ProductAttributeUpdate,
    ProductCategoryLinkResponse,
    ProductStoreResponse,
)
from src.product.service import ProductService

router = APIRouter(prefix="/product", tags=["Товари (Product)"])


async def _require_product(db: AsyncSession, product_id: int) -> None:
    if not await ProductService._ensure_product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Товар не знайдено")


@router.get("", response_model=List[ProductListItem])
async def get_products(
    category_id: Optional[int] = Query(None, description="Фільтр за ID категорії"),
    price_from: Optional[float] = Query(None, description="Ціна від"),
    price_to: Optional[float] = Query(None, description="Ціна до"),
    sort_by_name: Optional[str] = Query(None, description="Сортування за назвою ('asc' / 'desc')"),
    sort_by_price: Optional[str] = Query(None, description="Сортування за ціною ('asc' / 'desc')"),
    sort_by_category: Optional[str] = Query(
        None, description="Сортування за категорією — повний шлях ('asc' / 'desc')"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await ProductService.async_get_all_products(
        db,
        category_id,
        price_from,
        price_to,
        sort_by_name,
        sort_by_price,
        sort_by_category,
        page,
        limit,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await ProductService.async_get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не знайдено")
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await ProductService.async_create_product(db, product_data)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, update_data: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    product = await ProductService.async_update_product(db, product_id, update_data)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не знайдено")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    if not await ProductService.async_delete_product(db, product_id):
        raise HTTPException(status_code=404, detail="Товар не знайдено")
    return


@router.get("/{product_id}/image", response_model=List[ProductImageResponse])
async def get_product_images(product_id: int, db: AsyncSession = Depends(get_db)):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductImage).where(ProductImage.product_id == product_id)
    )
    return result.scalars().all()


@router.get("/{product_id}/image/{product_image_id}", response_model=ProductImageResponse)
async def get_product_image(
    product_id: int, product_image_id: int, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.product_image_id == product_image_id,
        )
    )
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Зображення не знайдено")
    return img


@router.post("/{product_id}/image", response_model=ProductImageResponse, status_code=201)
async def add_product_image(
    product_id: int, image_data: ProductImageCreate, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    new_img = ProductImage(product_id=product_id, **image_data.model_dump())
    db.add(new_img)
    await db.commit()
    await db.refresh(new_img)
    return new_img


@router.patch("/{product_id}/image/{product_image_id}", response_model=ProductImageResponse)
async def update_product_image(
    product_id: int,
    product_image_id: int,
    update_data: ProductImageUpdate,
    db: AsyncSession = Depends(get_db),
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.product_image_id == product_image_id,
        )
    )
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Зображення не знайдено")
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(img, key, value)
    await db.commit()
    await db.refresh(img)
    return img


@router.delete("/{product_id}/image/{product_image_id}", status_code=204)
async def delete_product_image(
    product_id: int, product_image_id: int, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.product_image_id == product_image_id,
        )
    )
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Зображення не знайдено")
    db.delete(img)
    await db.commit()
    return


@router.get("/{product_id}/attribute", response_model=List[ProductAttributeResponse])
async def get_product_attributes(product_id: int, db: AsyncSession = Depends(get_db)):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductAttribute).where(ProductAttribute.product_id == product_id)
    )
    return result.scalars().all()


@router.get(
    "/{product_id}/attribute/{product_attribute_id}",
    response_model=ProductAttributeResponse,
)
async def get_product_attribute(
    product_id: int, product_attribute_id: int, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductAttribute).where(
            ProductAttribute.product_id == product_id,
            ProductAttribute.product_attribute_id == product_attribute_id,
        )
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="Атрибут не знайдено")
    return attr


@router.post("/{product_id}/attribute", response_model=ProductAttributeResponse, status_code=201)
async def add_product_attribute(
    product_id: int, attr_data: ProductAttributeCreate, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    new_attr = ProductAttribute(product_id=product_id, **attr_data.model_dump())
    db.add(new_attr)
    await db.commit()
    await db.refresh(new_attr)
    return new_attr


@router.patch(
    "/{product_id}/attribute/{product_attribute_id}",
    response_model=ProductAttributeResponse,
)
async def update_product_attribute(
    product_id: int,
    product_attribute_id: int,
    update_data: ProductAttributeUpdate,
    db: AsyncSession = Depends(get_db),
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductAttribute).where(
            ProductAttribute.product_id == product_id,
            ProductAttribute.product_attribute_id == product_attribute_id,
        )
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="Атрибут не знайдено")
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(attr, key, value)
    await db.commit()
    await db.refresh(attr)
    return attr


@router.delete("/{product_id}/attribute/{product_attribute_id}", status_code=204)
async def delete_product_attribute(
    product_id: int, product_attribute_id: int, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductAttribute).where(
            ProductAttribute.product_id == product_id,
            ProductAttribute.product_attribute_id == product_attribute_id,
        )
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="Атрибут не знайдено")
    db.delete(attr)
    await db.commit()
    return


@router.get("/{product_id}/category", response_model=List[ProductCategoryLinkResponse])
async def get_product_categories(product_id: int, db: AsyncSession = Depends(get_db)):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.product_id == product_id)
    )
    links = result.scalars().all()
    return [await ProductService.build_category_link_response(db, link) for link in links]


@router.get(
    "/{product_id}/category/{product_category_id}",
    response_model=ProductCategoryLinkResponse,
)
async def get_product_category_link(
    product_id: int, product_category_id: int, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductCategory).where(
            ProductCategory.product_id == product_id,
            ProductCategory.product_category_id == product_category_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Зв'язок категорії не знайдено")
    return await ProductService.build_category_link_response(db, link)


@router.post("/{product_id}/category", response_model=ProductCategoryLinkResponse, status_code=201)
async def add_category_to_product(
    product_id: int,
    category_id: int = Query(..., description="ID категорії для прив'язки"),
    db: AsyncSession = Depends(get_db),
):
    await _require_product(db, product_id)
    link = ProductCategory(product_id=product_id, category_id=category_id)
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return await ProductService.build_category_link_response(db, link)


@router.delete("/{product_id}/category/{product_category_id}", status_code=204)
async def remove_category_from_product(
    product_id: int, product_category_id: int, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductCategory).where(
            ProductCategory.product_id == product_id,
            ProductCategory.product_category_id == product_category_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Зв'язок категорії не знайдено")
    db.delete(link)
    await db.commit()
    return


@router.get("/{product_id}/store", response_model=List[ProductStoreResponse])
async def get_product_stores(product_id: int, db: AsyncSession = Depends(get_db)):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductStore)
        .where(ProductStore.product_id == product_id)
        .options(selectinload(ProductStore.store))
    )
    links = result.scalars().all()
    return [
        ProductStoreResponse(
            product_store_id=link.product_store_id,
            product_id=link.product_id,
            store_id=link.store_id,
            store_name=link.store.name,
        )
        for link in links
    ]


@router.get(
    "/{product_id}/store/{product_store_id}",
    response_model=ProductStoreResponse,
)
async def get_product_store(
    product_id: int, product_store_id: int, db: AsyncSession = Depends(get_db)
):
    await _require_product(db, product_id)
    result = await db.execute(
        select(ProductStore)
        .where(
            ProductStore.product_id == product_id,
            ProductStore.product_store_id == product_store_id,
        )
        .options(selectinload(ProductStore.store))
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Зв'язок магазину не знайдено")
    return ProductStoreResponse(
        product_store_id=link.product_store_id,
        product_id=link.product_id,
        store_id=link.store_id,
        store_name=link.store.name,
    )
