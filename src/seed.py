import asyncio

from sqlalchemy import text

from src.database import SessionFactory, engine, Base
from src.category.models import CategoryStatus
from src.category.schemas import CategoryCreate
from src.category.service import CategoryService
from src.product.models import Manufacturer, Store
from src.product.schemas import (
    ProductCreate,
    ProductImageCreate,
    ProductAttributeCreate,
)
from src.product.service import ProductService


async def seed_data():
    import src.category.models
    import src.product.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionFactory() as db:
        print("🧹 Видаляємо старі дані з бази...")
        await db.execute(text("DELETE FROM product_store"))
        await db.execute(text("DELETE FROM product"))
        await db.execute(text("DELETE FROM store"))
        await db.execute(text("DELETE FROM manufacturer"))
        await db.execute(text("DELETE FROM category"))
        await db.commit()

        print("🌱 Починаємо заповнення бази мото-тематикою з ТЗ...")

        cat_moto = await CategoryService.async_create_category(
            db,
            CategoryCreate(name="Для мотоцикліста", parent_category_id=0, status=CategoryStatus.ENABLED),
        )
        cat_acc = await CategoryService.async_create_category(
            db,
            CategoryCreate(name="Аксесуари", parent_category_id=cat_moto.category_id, status=CategoryStatus.ENABLED),
        )
        cat_shoes = await CategoryService.async_create_category(
            db,
            CategoryCreate(name="Взуття", parent_category_id=cat_moto.category_id, status=CategoryStatus.ENABLED),
        )
        await CategoryService.async_create_category(
            db,
            CategoryCreate(name="Бестселери", parent_category_id=cat_moto.category_id, status=CategoryStatus.ENABLED),
        )
        cat_backpacks = await CategoryService.async_create_category(
            db,
            CategoryCreate(name="Рюкзаки", parent_category_id=cat_acc.category_id, status=CategoryStatus.ENABLED),
        )
        cat_balaclavas = await CategoryService.async_create_category(
            db,
            CategoryCreate(
                name="Балаклави та коміри", parent_category_id=cat_acc.category_id, status=CategoryStatus.ENABLED
            ),
        )
        await CategoryService.async_create_category(
            db,
            CategoryCreate(
                name="Накладки на коліна", parent_category_id=cat_acc.category_id, status=CategoryStatus.ENABLED
            ),
        )

        mfr_alpine = Manufacturer(name="Alpinestars")
        mfr_oxford = Manufacturer(name="Oxford")
        mfr_dainese = Manufacturer(name="Dainese")
        db.add_all([mfr_alpine, mfr_oxford, mfr_dainese])
        await db.commit()
        await db.refresh(mfr_alpine)
        await db.refresh(mfr_oxford)
        await db.refresh(mfr_dainese)

        store_kyiv = Store(name="Магазин Київ — Центр")
        store_lviv = Store(name="Магазин Львів")
        db.add_all([store_kyiv, store_lviv])
        await db.commit()
        await db.refresh(store_kyiv)
        await db.refresh(store_lviv)

        await ProductService.async_create_product(
            db,
            ProductCreate(
                name="Моторюкзак Alpinestars Aero",
                model="Aero Pack V2",
                price=3200.0,
                description="Аеродинамічний жорсткий рюкзак для їзди на спортбайку.",
                manufacturer_id=mfr_alpine.manufacturer_id,
                category_ids=[cat_acc.category_id, cat_backpacks.category_id],
                store_ids=[store_kyiv.store_id, store_lviv.store_id],
                images=[
                    ProductImageCreate(
                        image="https://images.example.com/backpack_front.jpg", sort_order=1
                    ),
                    ProductImageCreate(
                        image="https://images.example.com/backpack_inside.jpg", sort_order=2
                    ),
                ],
                attributes=[
                    ProductAttributeCreate(group_name="Розміри", name="Об'єм", value="25 літрів"),
                    ProductAttributeCreate(
                        group_name="Матеріал", name="Захист", value="Водонепроникний Oxford"
                    ),
                ],
            ),
        )

        await ProductService.async_create_product(
            db,
            ProductCreate(
                name="Балаклава літня Oxford Coolmax",
                model="Coolmax-2026",
                price=450.0,
                description="Повітропроникна підшоломна балаклава з ефектом охолодження.",
                manufacturer_id=mfr_oxford.manufacturer_id,
                category_ids=[cat_acc.category_id, cat_balaclavas.category_id],
                store_ids=[store_kyiv.store_id],
                images=[
                    ProductImageCreate(image="https://images.example.com/balaclava.jpg", sort_order=1),
                ],
                attributes=[
                    ProductAttributeCreate(group_name="Склад", name="Матеріал", value="100% Поліестер"),
                    ProductAttributeCreate(group_name="Загальне", name="Сезон", value="Літо"),
                ],
            ),
        )

        await ProductService.async_create_product(
            db,
            ProductCreate(
                name="Мотоботи Dainese Torque",
                model="Torque 3 Out",
                price=11500.0,
                description="Професійні спортивні мотоботи з трековим захистом гомілки.",
                manufacturer_id=mfr_dainese.manufacturer_id,
                category_ids=[cat_shoes.category_id],
                store_ids=[store_lviv.store_id],
                images=[
                    ProductImageCreate(image="https://images.example.com/boots.jpg", sort_order=1),
                ],
                attributes=[
                    ProductAttributeCreate(group_name="Безпека", name="Сертифікація", value="CE Cat. II"),
                    ProductAttributeCreate(
                        group_name="Матеріал", name="Основа", value="Мікрофібра та D-Stone"
                    ),
                ],
            ),
        )

        print("✅ Базу даних успішно зачищено та заселено тестовими даними з ТЗ!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
