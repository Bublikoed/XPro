from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class CategoryStatus(str, Enum):
    ENABLED = "1"
    DISABLED = "0"

class Category(Base):
    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    parent_category_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    seo_keyword: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_keyword: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[CategoryStatus] = mapped_column(
        String(1),
        default=CategoryStatus.ENABLED,
        server_default=text("'1'"),
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
