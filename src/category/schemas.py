from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from src.category.models import CategoryStatus


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Назва категорії")
    description: Optional[str] = Field(None, description="Опис категорії")
    parent_category_id: int = Field(default=0, description="ID батьківської категорії")
    seo_keyword: Optional[str] = Field(None, max_length=255)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None)
    meta_keyword: Optional[str] = Field(None, max_length=255)
    image: Optional[str] = Field(None, max_length=255)
    status: CategoryStatus = Field(default=CategoryStatus.ENABLED)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    seo_keyword: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keyword: Optional[str] = None
    image: Optional[str] = None
    status: Optional[CategoryStatus] = None


class CategoryResponse(CategoryBase):
    category_id: int
    date_added: datetime
    date_modify: datetime
    full_path: Optional[str] = Field(None, description="Повний шлях до категорії")

    model_config = {
        "from_attributes": True,
    }


class CategoryListItem(BaseModel):
    category_id: int
    name: str = Field(..., description="Повний шлях категорії в дереві")
    status: str = Field(..., description="Включена або Выключена")
