# Alkoteка Parser

Scrapy parser for alkoteka.com online store.

## Features

- Parses product data from multiple categories
- Region: Krasnodar (hardcoded)
- JavaScript rendering via Playwright
- Proxy support (configurable)
- JSON output

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
cd alkoteka
scrapy crawl alkoteka -O result.json
```

## Output Format

The parser outputs JSON with the following structure:

```json
{
    "timestamp": 1234567890,
    "RPC": "product-code",
    "url": "https://alkoteka.com/product/...",
    "title": "Product Name, 0.5L",
    "marketing_tags": ["Sale", "Popular"],
    "brand": "Brand Name",
    "section": ["Category", "Subcategory"],
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
        "__description": "Product description...",
        "Volume": "0.5L",
        "Country": "Germany"
    },
    "variants": 1
}
```

## Configuration

Edit `categories.txt` to change target categories:

```
https://alkoteka.com/catalog/slaboalkogolnye-napitki-2
https://alkoteka.com/catalog/pivo-1
https://alkoteka.com/catalog/vino-1
```

Add proxies in `settings.py`:

```python
PROXIES = [
    'http://user:pass@proxy1.com:8080',
    'http://user:pass@proxy2.com:8080',
]
```
