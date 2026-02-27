import scrapy
import json
import time
import re
import os
from urllib.parse import urljoin
from items import ProductItem


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka'
    allowed_domains = ['alkoteka.com']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy = None
        self._load_categories()

    def _load_categories(self):
        categories_file = os.path.join(os.path.dirname(__file__), '..', 'categories.txt')
        if os.path.exists(categories_file):
            with open(categories_file, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
            self.START_URLS = lines if lines else [
                'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',
                'https://alkoteka.com/catalog/pivo-1',
                'https://alkoteka.com/catalog/vino-1',
            ]
        else:
            self.START_URLS = [
                'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',
                'https://alkoteka.com/catalog/pivo-1',
                'https://alkoteka.com/catalog/vino-1',
            ]

    def start_requests(self):
        for url in self.START_URLS:
            yield scrapy.Request(url, callback=self.parse_category)

    def parse_category(self, response):
        section = self.extract_section(response.url)

        product_links = response.css('a[href*="/product/"]::attr(href)').getall()

        for link in product_links:
            url = urljoin('https://alkoteka.com', link)
            yield scrapy.Request(url, callback=self.parse_product, meta={'section': section})

        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield scrapy.Request(urljoin('https://alkoteka.com', next_page), 
                                callback=self.parse_category, 
                                meta={'section': section})

    def parse_product(self, response):
        section = response.meta.get('section', [])

        item = ProductItem()
        item['timestamp'] = int(time.time())
        
        rpc = response.css('[data-product-id]::attr(data-product-id)').get()
        if not rpc:
            match = re.search(r'/product/[^/]+/([^_]+)', response.url)
            if match:
                rpc = match.group(1)
            else:
                rpc_match = re.search(r'/product/(\d+)', response.url)
                rpc = str(rpc_match.group(1)) if rpc_match else ''
        item['RPC'] = str(rpc) if rpc else ''

        item['url'] = response.url

        title_parts = []
        name = response.css('h1::text').get()
        if name:
            name = name.strip()
            title_parts.append(name)
        
        volume = response.css('[class*="volume"]::text, [class*="size"]::text').re_first(r'\d+[\.,]?\d*\s*(л|мл|г|кг|ml|l|g|kg)')
        if volume:
            title_parts.append(volume.strip())
        
        color = response.css('[class*="color"]::text').get()
        if color:
            title_parts.append(color.strip())
        
        item['title'] = ', '.join(title_parts) if title_parts else (name or '')

        tags = []
        badge_text = response.css('[class*="badge"]::text').getall()
        for t in badge_text:
            t = t.strip()
            if t and len(t) < 30:
                tags.append(t)
        
        item['marketing_tags'] = tags

        description = response.css('[class*="description-text"]::text, [class*="description"] p::text').getall()
        description_text = ' '.join([d.strip() for d in description if d.strip()])

        metadata = {'__description': description_text}

        brand = ''
        
        specs = response.css('.specifications-card')
        for spec in specs:
            key = spec.css('span::text').get()
            value = spec.css('.text--body::text').get()
            
            if key and value:
                key = key.strip()
                value = value.strip()
                
                if 'бренд' in key.lower():
                    brand = value
                elif key:
                    if len(key) < 50 and len(value) < 100:
                        metadata[key] = value
        
        if not brand:
            brand_el = response.css('.product-info__title::text, [class*="product-title"]::text').get()
            if brand_el and len(brand_el.strip()) < 50:
                brand = brand_el.strip()
        
        item['brand'] = brand
        
        item['section'] = section

        price_text = response.css('.text--button-price::text').getall()
        prices = []
        for pt in price_text:
            nums = re.findall(r'\d+', pt)
            for n in nums:
                try:
                    p = float(n)
                    if p > 0:
                        prices.append(p)
                except:
                    pass
        
        current_price = prices[0] if prices else 0.0
        original_price = prices[-1] if len(prices) > 1 else current_price
        
        sale_tag = ''
        if original_price > current_price and current_price > 0:
            discount = int((1 - current_price / original_price) * 100)
            sale_tag = f"Скидка {discount}%"

        item['price_data'] = {
            'current': current_price,
            'original': original_price,
            'sale_tag': sale_tag
        }

        in_stock = True
        stock_count = 0
        
        unavailable = response.css('[class*="unavailable"]::text, [class*="disabled"]::text').get()
        if unavailable and 'нет' in unavailable.lower():
            in_stock = False

        item['stock'] = {
            'in_stock': in_stock,
            'count': stock_count
        }

        main_image = response.css('[class*="preview"] img::attr(src), .product-info img::attr(src)').get()
        if main_image:
            if not main_image.startswith('http'):
                main_image = urljoin('https://alkoteka.com', main_image)
        else:
            main_image = ''

        item['assets'] = {
            'main_image': main_image,
            'set_images': [],
            'view360': [],
            'video': []
        }

        description = response.css('[class*="description-text"]::text, [class*="description"] p::text').getall()
        description = ' '.join([d.strip() for d in description if d.strip()])

        metadata = {'__description': description}

        item['metadata'] = metadata

        item['variants'] = 1

        yield item

    def extract_section(self, url):
        section = []
        path = url.replace('https://alkoteka.com/catalog/', '')
        parts = path.split('/')
        for part in parts:
            if part and part != 'catalog':
                name = part.replace('-', ' ').replace('_', ' ').title()
                section.append(name)
        return section
