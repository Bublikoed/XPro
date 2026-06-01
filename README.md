# E-Commerce API

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-red)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-Collection-FF6C37?logo=postman&logoColor=white)

**Репозиторій:** [github.com/Bublikoed/XPro](https://github.com/Bublikoed/XPro)

Асинхронний REST API інтернет-магазину: модулі **category** (дерево категорій) та **product** (товари з фото, атрибутами та зв’язками з категоріями). Увесь стек піднімається через **Docker Compose** — локально не потрібні Python, pip чи MySQL. Тестові дані (мото-тематика з ТЗ) заливаються однією командою сідера.

---

## Технологічний стек

| Шар | Технології |
|-----|------------|
| **API** | [FastAPI](https://fastapi.tiangolo.com/), Uvicorn |
| **Валідація** | [Pydantic v2](https://docs.pydantic.dev/) |
| **ORM** | [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) (async, `Mapped` / `mapped_column`) |
| **БД** | MySQL 8.0, [aiomysql](https://github.com/aio-libs/aiomysql) |
| **Інфраструктура** | Docker, Docker Compose |
| **Адмінка БД** | phpMyAdmin |

---

## Що потрібно перед стартом

1. Встановлений [Docker Desktop](https://www.docker.com/products/docker-desktop/) (або Docker Engine + Compose v2).
2. Вільні порти на машині: **8000** (API), **8080** (phpMyAdmin), за бажанням **3306** (MySQL).
3. Git для клонування репозиторію.

> Файл `.env` **не потрапляє в Git** (див. `.gitignore`). У репозиторії є шаблон **`env.example`** — з нього створюється локальна конфігурація.

---

## Запуск проєкту

Скопіюйте блок команд у термінал — цього достатньо для першого запуску.

```bash
# 1. Клонування
git clone https://github.com/Bublikoed/XPro.git
cd XPro

# 2. Локальний конфіг (обов'язково!)
cp env.example .env
```

Шаблон `env.example` уже містить пароль `shop_password`, узгоджений з `docker-compose.yml`. Після `cp` нічого міняти не потрібно.

> Якщо зміните пароль у `.env`, оновіть також `MYSQL_ROOT_PASSWORD` і healthcheck у `docker-compose.yml` (сервіс `db`).

```bash
# 3. Збірка та запуск у фоні
docker compose up --build -d

# 4. Перевірка (db має бути healthy)
docker compose ps

# 5. Демо-дані (категорії + товари)
docker compose run --rm seed
```

### Як переконатися, що все працює

| Крок | Дія | Очікуваний результат |
|------|-----|----------------------|
| 1 | Відкрити [http://localhost:8000/healthcheck](http://localhost:8000/healthcheck) | JSON з `"status": "online"` |
| 2 | Відкрити [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI |
| 3 | `GET /category` у Swagger | Список категорій з `full_path` (наприклад, `Для мотоцикліста > Аксесуари > Рюкзаки`) |
| 4 | Імпорт колекції Postman (див. нижче) | Запити `category`, `product`, `healthcheck` відповідають 200 |
| 5 | [http://localhost:8080](http://localhost:8080) | phpMyAdmin, база `shop_db` |

Після успішного сідера в терміналі:

```text
🧹 Видаляємо старі дані з бази...
🌱 Починаємо заповнення бази мото-тематикою з ТЗ...
✅ Базу даних успішно зачищено та заселено тестовими даними з ТЗ!
```

---

## Локальні сервіси

| Сервіс | URL | Доступ |
|--------|-----|--------|
| **API через Apache2** | [http://localhost/docs](http://localhost/docs) | Reverse-proxy (ТЗ); той самий Swagger |
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Прямий доступ до Uvicorn |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Альтернативна документація |
| **Healthcheck** | [http://localhost:8000/healthcheck](http://localhost:8000/healthcheck) | Статус застосунку |
| **phpMyAdmin** | [http://localhost:8080](http://localhost:8080) | Логін: `root`, пароль: `shop_password`, БД: `shop_db` |

У phpMyAdmin хост БД уже заданий як `db` (ім’я сервісу в Docker-мережі).

---

## Тестування API через Postman

У корені репозиторію лежить готова колекція **`FastAPI_Shop.postman_collection.json`** — усі ендпоінти з OpenAPI (модулі **category**, **product**, **healthcheck**).

### Імпорт

1. Встановіть [Postman](https://www.postman.com/downloads/) (Desktop або веб).
2. **Import** → оберіть файл `FastAPI_Shop.postman_collection.json` з клонованого репозиторію.
3. Відкрийте колекцію **FastAPI_Shop** → вкладка **Variables**.
4. Встановіть змінну **`baseUrl`**:

   ```text
   http://localhost:8000
   ```

   (У файлі за замовчуванням може бути `/` — для локального Docker потрібен повний URL.)

5. Запустіть `docker compose up -d` і `docker compose run --rm seed`, потім виконуйте запити з колекції.

> **Порада:** після сідера підставляйте реальні `category_id` / `product_id` з відповіді `GET /category` або phpMyAdmin — у прикладах колекції можуть бути довільні значення-заглушки.

Альтернатива Swagger — [http://localhost:8000/docs](http://localhost:8000/docs); Postman зручний для збереження сценаріїв перевірки та демо тімліду.

---

## Docker Compose: сервіси

| Сервіс | Призначення | Порт на хості |
|--------|-------------|---------------|
| `web` | FastAPI + Uvicorn (hot reload) | `8000` |
| `db` | MySQL 8.0 | `3306` |
| `phpmyadmin` | Адмін-панель БД | `8080` |
| `apache` | Apache 2.4 → проксі на `web:8000` | `80` |
| `seed` | Скрипт `src/seed.py` (запускається вручну) | — |

---

## Повне скидання бази (опційно)

Якщо потрібна чиста MySQL (видаляється volume з даними):

```bash
docker compose down -v
docker compose up --build -d
docker compose run --rm seed
```

Повторний сідер **без** `-v` лише очищає таблиці `product` і `category` і заливає дані заново — цього зазвичай достатньо після змін у `src/seed.py`.

---

## Структура репозиторію

```text
XPro/
├── docker-compose.yml    # web, db, phpmyadmin, seed
├── Dockerfile
├── env.example                          # шаблон змінних (копіювати в .env)
├── FastAPI_Shop.postman_collection.json # Postman: category, product, healthcheck
├── .gitignore                           # .env, __pycache__, .DS_Store
├── README.md
└── src/
    ├── main.py           # FastAPI, створення таблиць при старті
    ├── config.py
    ├── database.py       # Async engine, SessionFactory
    ├── seed.py           # демо-дані (мото-тематика)
    ├── category/         # router, service, schemas, models
    └── product/
```

---

## Реалізовані можливості (ТЗ)

### Категорії (`/category`)

- Рекурсивні шляхи у полі **`full_path`** (`Для мотоцикліста > Аксесуари > Рюкзаки`).
- Сортування за повним шляхом: `sort_by_name=asc|desc`.
- Пошук і фільтри за id, назвою, статусом; пагінація `page` / `limit`.
- Каскадне видалення підкатегорій при `DELETE /category/{id}`.
- Автоматичні `date_added` / `date_modify` (MySQL `CURRENT_TIMESTAMP`).

### Товари (`/product`)

- Список: `product_id`, `name`, `categories` (повні шляхи), `price`.
- CRUD; при створенні — лише **назва** обов’язкова, **статус 0** за замовчуванням.
- Вкладені CRUD: `image`, `attribute`, `category` (за `product_category_id`), **store**.
- Деталізація: виробник (`manufacturer`), магазини з назвами, категорії з `full_path`.
- Сортування: назва, ціна, **категорія** (`sort_by_category`).

### Технічно

- Асинхронні роути та сервіси (`async` / `await`).
- Pydantic v2, SQLAlchemy 2.0 style models.
- Залежності та runtime — лише в Docker-образі.

---

## Корисні команди

```bash
# Логи API в реальному часі
docker compose logs -f web

# Логи MySQL
docker compose logs -f db

# Зупинити проєкт
docker compose down

# Перезапустити API після змін коду
docker compose restart web
```

---

## Типові проблеми

| Симптом | Рішення |
|---------|---------|
| `ModuleNotFoundError: No module named 'src'` при сідері | Запускайте `docker compose run --rm seed`, не `python src/seed.py` локально без `PYTHONPATH` |
| API не підключається до БД | Перевірте, що в `.env` пароль `shop_password`, як у `docker-compose.yml` |
| phpMyAdmin не відкривається | Використовуйте **http://localhost:8080**, не порт 80 |
| Порожній Swagger після клону | Виконайте `docker compose run --rm seed` |
| Порт зайнятий | Змініть мапінг у `docker-compose.yml` (наприклад, `"8001:8000"`) |

---

## Ліцензія

Навчальний / тестовий проєкт для перевірки ТЗ. Деталі — за домовленістю з командою.
