from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class ProductStatus(str, Enum):
    ENABLED = "1"
    DISABLED = "0"


class Manufacturer(Base):
    __tablename__ = "manufacturer"

    manufacturer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Store(Base):
    __tablename__ = "store"

    store_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class ProductCategory(Base):
    __tablename__ = "product_category"

    product_category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.product_id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("category.category_id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("product_id", "category_id", name="uq_product_category"),
    )


class ProductImage(Base):
    __tablename__ = "product_image"

    product_image_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.product_id", ondelete="CASCADE"), nullable=False
    )
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    product: Mapped["Product"] = relationship(back_populates="images")


class ProductAttribute(Base):
    __tablename__ = "product_attribute"

    product_attribute_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.product_id", ondelete="CASCADE"), nullable=False
    )
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    product: Mapped["Product"] = relationship(back_populates="attributes")


class ProductStore(Base):
    __tablename__ = "product_store"

    product_store_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.product_id", ondelete="CASCADE"), nullable=False
    )
    store_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("store.store_id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("product_id", "store_id", name="uq_product_store"),
    )

    store: Mapped["Store"] = relationship("Store")


class Product(Base):
    __tablename__ = "product"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_keyword: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_keyword: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    model: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default=text("''"))
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default=text("0"))
    manufacturer_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    rating: Mapped[float] = mapped_column(Float, default=0.0, server_default=text("0"))
    viewed: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    status: Mapped[ProductStatus] = mapped_column(
        String(1),
        default=ProductStatus.DISABLED,
        server_default=text("'0'"),
    )

    date_added: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    date_modify: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        onupdate=datetime.now,
    )

    manufacturer: Mapped[Optional["Manufacturer"]] = relationship(
        "Manufacturer",
        primaryjoin="and_(Product.manufacturer_id == Manufacturer.manufacturer_id, Product.manufacturer_id != 0)",
        foreign_keys="Product.manufacturer_id",
        viewonly=True,
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary="product_category",
        lazy="selectin",
    )
    images: Mapped[List["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    attributes: Mapped[List["ProductAttribute"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    product_stores: Mapped[List["ProductStore"]] = relationship(
        "ProductStore",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
