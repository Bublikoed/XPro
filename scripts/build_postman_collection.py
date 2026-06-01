#!/usr/bin/env python3
"""Generate FastAPI.postman_collection.json with variables and runner-friendly order."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "FastAPI.postman_collection.json"

SAVE_STORE_FROM_LIST = """
if (pm.response.code === 200) {
    const arr = pm.response.json();
    if (Array.isArray(arr) && arr.length && arr[0].product_store_id != null) {
        pm.collectionVariables.set("storeLinkId", String(arr[0].product_store_id));
    }
}
""".strip()


def test_script(*lines: str) -> list[dict]:
    exec_lines = [line for line in lines if line]
    if not exec_lines:
        return []
    return [
        {
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": exec_lines,
            },
        }
    ]


def headers_json() -> list[dict]:
    return [
        {"key": "Accept", "value": "application/json"},
        {"key": "Content-Type", "value": "application/json"},
    ]


def headers_accept() -> list[dict]:
    return [{"key": "Accept", "value": "application/json"}]


def url(
    path_segments: list,
    query: Optional[list] = None,
    path_vars: Optional[dict] = None,
) -> dict:
    variables = []
    resolved = []
    for seg in path_segments:
        if seg.startswith(":"):
            key = seg[1:]
            val = (path_vars or {}).get(key, f"{{{{{key}}}}}")
            variables.append({"key": key, "value": val})
            resolved.append(f":{key}")
        else:
            resolved.append(seg)
    raw = "{{baseUrl}}/" + "/".join(resolved)
    active_query = [p for p in (query or []) if not p.get("disabled")]
    if active_query:
        q = "&".join(f"{p['key']}={p['value']}" for p in active_query)
        raw = raw + "?" + q
    result: dict = {
        "raw": raw,
        "host": ["{{baseUrl}}"],
        "path": resolved,
    }
    if query:
        result["query"] = query
    if variables:
        result["variable"] = variables
    return result


def body_raw(raw: str) -> dict:
    return {
        "mode": "raw",
        "raw": raw,
        "options": {"raw": {"language": "json"}},
    }


def request_item(
    name: str,
    method: str,
    path_segments: list,
    *,
    body: Optional[str] = None,
    query: Optional[list] = None,
    path_vars: Optional[dict] = None,
    tests: Optional[list] = None,
    json_headers: bool = True,
) -> dict:
    item: dict = {
        "name": name,
        "request": {
            "method": method,
            "header": headers_json() if json_headers and body else headers_accept(),
            "url": url(path_segments, query=query, path_vars=path_vars),
        },
    }
    if body is not None:
        item["request"]["header"] = headers_json()
        item["request"]["body"] = body_raw(body)
    elif method in ("POST", "PATCH", "PUT") and query:
        item["request"]["header"] = headers_accept()
    if tests:
        item["event"] = test_script(*tests)
    return item


def build() -> dict:
    cat_path = {"category_id": "{{catId}}"}
    prod_path = {"product_id": "{{prodId}}"}
    img_path = {**prod_path, "product_image_id": "{{imageId}}"}
    attr_path = {**prod_path, "product_attribute_id": "{{attrId}}"}
    pcat_path = {**prod_path, "product_category_id": "{{prodCatId}}"}
    store_path = {**prod_path, "product_store_id": "{{storeLinkId}}"}

    category_items = [
        request_item(
            "1. Create Category",
            "POST",
            ["category"],
            body=json.dumps(
                {
                    "name": "Postman тестова категорія",
                    "description": "Створено з колекції Postman",
                    "parent_category_id": 0,
                    "status": "1",
                },
                ensure_ascii=False,
                indent=2,
            ),
            tests=[
                "pm.test('Created', () => pm.response.to.have.status(201));",
                "const j = pm.response.json();",
                'pm.collectionVariables.set("catId", String(j.category_id));',
            ],
        ),
        request_item(
            "2. Get Category",
            "GET",
            ["category", ":category_id"],
            path_vars=cat_path,
            tests=["pm.test('OK', () => pm.response.to.have.status(200));"],
        ),
        request_item(
            "3. Update Category",
            "PATCH",
            ["category", ":category_id"],
            path_vars=cat_path,
            body=json.dumps(
                {"description": "Оновлено через Postman", "seo_keyword": "postman-test"},
                ensure_ascii=False,
                indent=2,
            ),
            tests=["pm.test('OK', () => pm.response.to.have.status(200));"],
        ),
        request_item(
            "4. Get Categories (list)",
            "GET",
            ["category"],
            query=[
                {"key": "page", "value": "1", "description": "Номер сторінки"},
                {"key": "limit", "value": "20", "description": "Ліміт"},
                {"key": "search_id", "value": "{{catId}}", "disabled": True},
                {"key": "search_name", "value": "", "disabled": True},
                {"key": "status_filter", "value": "", "disabled": True},
                {"key": "sort_by_name", "value": "", "disabled": True},
                {"key": "sort_by_id", "value": "", "disabled": True},
            ],
        ),
        request_item(
            "5. Delete Category",
            "DELETE",
            ["category", ":category_id"],
            path_vars=cat_path,
            tests=["pm.test('No Content', () => pm.response.to.have.status(204));"],
        ),
    ]

    product_items = [
        request_item(
            "1. Create Product",
            "POST",
            ["product"],
            body=(
                "{\n"
                '  "name": "Postman тестовий товар",\n'
                '  "status": "0",\n'
                '  "price": 99.99,\n'
                '  "description": "Мінімальне створення для сценарію Postman",\n'
                '  "manufacturer_id": {{manufacturerId}}\n'
                "}"
            ),
            tests=[
                "pm.test('Created', () => pm.response.to.have.status(201));",
                'pm.collectionVariables.set("prodId", String(pm.response.json().product_id));',
            ],
        ),
        request_item(
            "2. Get Product",
            "GET",
            ["product", ":product_id"],
            path_vars=prod_path,
            tests=[
                "pm.test('OK', () => pm.response.to.have.status(200));",
                "const j = pm.response.json();",
                "if (j.stores && j.stores.length) {",
                '    pm.collectionVariables.set("storeLinkId", String(j.stores[0].product_store_id));',
                "}",
            ],
        ),
        request_item(
            "3. Update Product",
            "PATCH",
            ["product", ":product_id"],
            path_vars=prod_path,
            body=json.dumps({"price": 149.99, "description": "Оновлено через Postman"}, ensure_ascii=False, indent=2),
        ),
        request_item(
            "4. Get Products (list)",
            "GET",
            ["product"],
            query=[
                {"key": "page", "value": "1"},
                {"key": "limit", "value": "20"},
                {"key": "category_id", "value": "{{catId}}", "disabled": True},
                {"key": "price_from", "value": "", "disabled": True},
                {"key": "price_to", "value": "", "disabled": True},
                {"key": "sort_by_name", "value": "", "disabled": True},
                {"key": "sort_by_price", "value": "", "disabled": True},
                {"key": "sort_by_category", "value": "", "disabled": True},
            ],
        ),
        {
            "name": "5. Images",
            "item": [
                request_item(
                    "5.1 Add Product Image",
                    "POST",
                    ["product", ":product_id", "image"],
                    path_vars=prod_path,
                    body=json.dumps({"image": "catalog/postman-test.jpg", "sort_order": 1}, indent=2),
                    tests=[
                        'pm.collectionVariables.set("imageId", String(pm.response.json().product_image_id));',
                    ],
                ),
                request_item(
                    "5.2 Get Product Images",
                    "GET",
                    ["product", ":product_id", "image"],
                    path_vars=prod_path,
                ),
                request_item(
                    "5.3 Get Product Image",
                    "GET",
                    ["product", ":product_id", "image", ":product_image_id"],
                    path_vars=img_path,
                ),
                request_item(
                    "5.4 Update Product Image",
                    "PATCH",
                    ["product", ":product_id", "image", ":product_image_id"],
                    path_vars=img_path,
                    body=json.dumps({"sort_order": 2}, indent=2),
                ),
                request_item(
                    "5.5 Delete Product Image",
                    "DELETE",
                    ["product", ":product_id", "image", ":product_image_id"],
                    path_vars=img_path,
                ),
            ],
        },
        {
            "name": "6. Attributes",
            "item": [
                request_item(
                    "6.1 Add Product Attribute",
                    "POST",
                    ["product", ":product_id", "attribute"],
                    path_vars=prod_path,
                    body=json.dumps(
                        {
                            "group_name": "Загальні",
                            "name": "Матеріал",
                            "value": "Текстиль",
                            "sort_order": 0,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    tests=[
                        'pm.collectionVariables.set("attrId", String(pm.response.json().product_attribute_id));',
                    ],
                ),
                request_item(
                    "6.2 Get Product Attributes",
                    "GET",
                    ["product", ":product_id", "attribute"],
                    path_vars=prod_path,
                ),
                request_item(
                    "6.3 Get Product Attribute",
                    "GET",
                    ["product", ":product_id", "attribute", ":product_attribute_id"],
                    path_vars=attr_path,
                ),
                request_item(
                    "6.4 Update Product Attribute",
                    "PATCH",
                    ["product", ":product_id", "attribute", ":product_attribute_id"],
                    path_vars=attr_path,
                    body=json.dumps({"value": "Шкіра"}, ensure_ascii=False, indent=2),
                ),
                request_item(
                    "6.5 Delete Product Attribute",
                    "DELETE",
                    ["product", ":product_id", "attribute", ":product_attribute_id"],
                    path_vars=attr_path,
                ),
            ],
        },
        {
            "name": "7. Product ↔ Category",
            "item": [
                request_item(
                    "7.1 Add Category To Product",
                    "POST",
                    ["product", ":product_id", "category"],
                    path_vars=prod_path,
                    query=[{"key": "category_id", "value": "{{catId}}", "description": "ID категорії"}],
                    tests=[
                        'pm.collectionVariables.set("prodCatId", String(pm.response.json().product_category_id));',
                    ],
                ),
                request_item(
                    "7.2 Get Product Categories",
                    "GET",
                    ["product", ":product_id", "category"],
                    path_vars=prod_path,
                ),
                request_item(
                    "7.3 Get Product Category Link",
                    "GET",
                    ["product", ":product_id", "category", ":product_category_id"],
                    path_vars=pcat_path,
                ),
                request_item(
                    "7.4 Remove Category From Product",
                    "DELETE",
                    ["product", ":product_id", "category", ":product_category_id"],
                    path_vars=pcat_path,
                ),
            ],
        },
            {
                "name": "8. Stores (read-only)",
                "description": "Після seed: увімкніть store_ids у Create Product або підставте storeId з phpMyAdmin (таблиця store).",
                "item": [
                    request_item(
                        "8.1 Get Product Stores",
                        "GET",
                        ["product", ":product_id", "store"],
                        path_vars=prod_path,
                        tests=[SAVE_STORE_FROM_LIST],
                    ),
                    request_item(
                        "8.2 Get Product Store Link",
                        "GET",
                        ["product", ":product_id", "store", ":product_store_id"],
                        path_vars=store_path,
                    ),
                ],
            },
        request_item(
            "9. Delete Product",
            "DELETE",
            ["product", ":product_id"],
            path_vars=prod_path,
            tests=["pm.test('No Content', () => pm.response.to.have.status(204));"],
        ),
    ]

    return {
        "info": {
            "name": "FastAPI Shop",
            "description": "E-Commerce API: category & product. Запускайте папки по порядку (Collection Runner).\n\nПеред тестами: docker compose up -d && docker compose run --rm seed\n\nЗмінні: baseUrl, catId, prodId, imageId, attrId, prodCatId, storeLinkId, manufacturerId, storeId (після seed зазвичай 1).",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000", "type": "string"},
            {"key": "catId", "value": "", "type": "string"},
            {"key": "prodId", "value": "", "type": "string"},
            {"key": "imageId", "value": "", "type": "string"},
            {"key": "attrId", "value": "", "type": "string"},
            {"key": "prodCatId", "value": "", "type": "string"},
            {"key": "storeLinkId", "value": "", "type": "string"},
            {"key": "manufacturerId", "value": "1", "type": "string"},
            {
                "key": "storeId",
                "value": "1",
                "type": "string",
                "description": "ID з таблиці store після seed (перевірте в phpMyAdmin)",
            },
        ],
        "item": [
            {
                "name": "healthcheck",
                "item": [
                    request_item("Healthcheck", "GET", ["healthcheck"], json_headers=False),
                ],
            },
            {"name": "category", "description": "Сценарій: Create → Get → Update → List → Delete", "item": category_items},
            {
                "name": "product",
                "description": "Сценарій після category (потрібен catId для 7.1). Create → … → Delete",
                "item": product_items,
            },
        ],
    }


def main() -> None:
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
