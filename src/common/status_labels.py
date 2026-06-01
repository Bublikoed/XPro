from src.category.models import CategoryStatus
from src.product.models import ProductStatus

CATEGORY_STATUS_LABELS = {
    CategoryStatus.ENABLED: "Включена",
    CategoryStatus.DISABLED: "Выключена",
}

PRODUCT_STATUS_LABELS = {
    ProductStatus.ENABLED: "Включена",
    ProductStatus.DISABLED: "Выключена",
}


def _resolve_status(status, labels: dict, enum_cls):
    if isinstance(status, enum_cls):
        return labels.get(status, str(status.value))
    try:
        return labels.get(enum_cls(status), str(status))
    except ValueError:
        return str(status)


def category_status_label(status) -> str:
    return _resolve_status(status, CATEGORY_STATUS_LABELS, CategoryStatus)


def product_status_label(status) -> str:
    return _resolve_status(status, PRODUCT_STATUS_LABELS, ProductStatus)
