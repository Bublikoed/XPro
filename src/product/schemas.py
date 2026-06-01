from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.category.schemas import CategoryResponse
from src.product.models import ProductStatus


class ProductImageBase(BaseModel):
    image: str = Field(..., description="Шлях до зображення")
    sort_order: int = Field(default=0)


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageUpdate(BaseModel):
    sort_order: Optional[int] = None


class ProductImageResponse(ProductImageBase):
    product_image_id: int
    product_id: int

    model_config = {"from_attributes": True}


class ProductAttributeBase(BaseModel):
    group_name: str
    name: str
    value: str
    sort_order: int = 0


class ProductAttributeCreate(ProductAttributeBase):
    pass


class ProductAttributeUpdate(BaseModel):
    group_name: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None
    sort_order: Optional[int] = None


class ProductAttributeResponse(ProductAttributeBase):
    product_attribute_id: int
    product_id: int

    model_config = {"from_attributes": True}


class ManufacturerResponse(BaseModel):
    manufacturer_id: int
    name: str

    model_config = {"from_attributes": True}


class ProductStoreResponse(BaseModel):
    product_store_id: int
    product_id: int
    store_id: int
    store_name: str = Field(..., description="Назва магазину")

    model_config = {"from_attributes": True}


class ProductCategoryLinkResponse(BaseModel):
    product_category_id: int
    product_id: int
    category_id: int
    category_name: str = Field(..., description="Повний шлях категорії")

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    product_id: int
    name: str
    category: str = Field(default="", description="Категорія товару (повний шлях)")
    price: float


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    status: ProductStatus = Field(default=ProductStatus.DISABLED)
    description: Optional[str] = None
    seo_keyword: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keyword: Optional[str] = None
    image: Optional[str] = None
    price: float = Field(default=0.0, ge=0.0)
    model: Optional[str] = Field(default="", max_length=255)
    manufacturer_id: Optional[int] = None
    category_ids: List[int] = Field(default_factory=list)
    store_ids: List[int] = Field(default_factory=list)
    images: List[ProductImageCreate] = Field(default_factory=list)
    attributes: List[ProductAttributeCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    seo_keyword: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keyword: Optional[str] = None
    image: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.0)
    model: Optional[str] = None
    manufacturer_id: Optional[int] = None
    status: Optional[ProductStatus] = None


class ProductResponse(BaseModel):
    product_id: int
    name: str
    description: Optional[str] = None
    seo_keyword: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keyword: Optional[str] = None
    image: Optional[str] = None
    price: float
    model: str
    manufacturer_id: Optional[int] = None
    status: ProductStatus
    status_label: str
    rating: float
    viewed: int
    date_added: datetime
    date_modify: datetime
    manufacturer: Optional[ManufacturerResponse] = None
    categories: List[CategoryResponse] = []
    images: List[ProductImageResponse] = []
    attributes: List[ProductAttributeResponse] = []
    stores: List[ProductStoreResponse] = []

    model_config = {"from_attributes": True}
