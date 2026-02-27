# Парсер alkoteka.com

Scrapy-парсер для сбора данных о товарах с интернет-магазина alkoteka.com.

## Возможности

- Парсинг товаров из нескольких категорий
- Рендеринг JavaScript через Playwright
- Регион: Краснодар (hardcoded)
- Поддержка прокси
- Сохранение в JSON

## Требования

```bash
pip install -r requirements.txt
playwright install chromium
```

## Использование

```bash
cd alkoteka
scrapy crawl alkoteka -O result.json
```

## Настройка категорий

Отредактируйте файл `categories.txt`:

```
https://alkoteka.com/catalog/slaboalkogolnye-napitki-2
https://alkoteka.com/catalog/pivo-1
https://alkoteka.com/catalog/vino-1
```

## Настройка прокси

Добавьте прокси в `settings.py`:

```python
PROXIES = [
    'http://user:pass@proxy1.com:8080',
    'http://user:pass@proxy2.com:8080',
]
```

## Формат выходных данных

```json
{
    "timestamp": 1234567890,
    "RPC": "product-code",
    "url": "https://alkoteka.com/product/...",
    "title": "Название товара, 0.5л",
    "marketing_tags": ["Акция", "Популярный"],
    "brand": "Название бренда",
    "section": ["Категория", "Подкатегория"],
    "price_data": {
        "current": 199.0,
        "original": 299.0,
        "sale_tag": "Скидка 33%"
    },
    "stock": {
        "in_stock": true,
        "count": 10
    },
    "assets": {
        "main_image": "https://...",
        "set_images": [],
        "view360": [],
        "video": []
    },
    "metadata": {
        "__description": "Описание товара",
        "Объем": "0.5 л",
        "Страна производитель": "Германия"
    },
    "variants": 1
}
```

## Структура проекта

```
alkoteka/
├── __init__.py
├── items.py          # Модель данных
├── middlewares.py    # Playwright + Proxy middleware
├── pipelines.py      # Сохранение в JSON
├── settings.py       # Настройки
├── categories.txt    # Список категорий
├── spiders/
│   ├── __init__.py
│   └── alkoteka_spider.py  # Паук
├── scrapy.cfg
├── requirements.txt
└── README.md
```

## Дополнительные параметры

```bash
# Изменить количество потоков
scrapy crawl alkoteka -s CONCURRENT_REQUESTS=1

# Изменить задержку между запросами
scrapy crawl alkoteka -s DOWNLOAD_DELAY=2

# Отключить троттлинг
scrapy crawl alkoteka -s AUTOTHROTTLE_ENABLED=False

# Уровень логирования
scrapy crawl alkoteka -s LOG_LEVEL=INFO
```
