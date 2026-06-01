from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.database import Base, engine
from src.category.router import router as category_router
from src.product.router import router as product_router

SHOW_DOCS_IN = {"local", "staging"}
app_kwargs = {"title": "E-Commerce API (Category & Product)"}

if settings.ENVIRONMENT not in SHOW_DOCS_IN:
    app_kwargs["openapi_url"] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    import src.category.models
    import src.product.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(**app_kwargs, lifespan=lifespan)

app.include_router(category_router)
app.include_router(product_router)


@app.get("/healthcheck")
async def healthcheck():
    return {
        "status": "online",
        "message": "Система працює, модулі category та product успішно підключено!",
    }
