# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import HtmlResponse
from playwright.async_api import async_playwright
import asyncio

from itemadapter import ItemAdapter


class AlkotekaSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    async def process_start(self, start):
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class AlkotekaDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class PlaywrightMiddleware:
    """Middleware to render JavaScript using Playwright"""

    def __init__(self, crawler):
        self.crawler = crawler
        self.region = crawler.settings.get('REGION', 'Krasnodar')
        self.city_id = crawler.settings.get('CITY_ID', '117274')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    async def process_request(self, request, spider):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-gpu', '--no-sandbox']
                )
                context = await browser.new_context()
                
                await context.add_cookies([
                    {"name": "city", "value": self.city_id, "domain": "alkoteka.com", "path": "/"},
                    {"name": "region", "value": "3", "domain": "alkoteka.com", "path": "/"},
                ])

                page = await context.new_page()

                try:
                    await page.goto(request.url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(2000)
                    
                    if '/catalog/' in request.url:
                        for _ in range(2):
                            try:
                                await page.evaluate('window.scrollBy(0, 1000)')
                                await page.wait_for_timeout(300)
                            except:
                                pass

                    content = await page.content()
                finally:
                    try:
                        await page.close()
                    except:
                        pass
                    try:
                        await context.close()
                    except:
                        pass
                    try:
                        await browser.close()
                    except:
                        pass

                return HtmlResponse(
                    url=request.url,
                    body=content,
                    encoding='utf-8',
                    request=request
                )
        except Exception as e:
            spider.logger.error(f"Playwright error: {e}")
            return None


class ProxyMiddleware:
    """Middleware to rotate proxies"""

    def __init__(self, crawler):
        self.crawler = crawler
        self.proxies = crawler.settings.getlist('PROXIES', [])
        self.current_proxy_index = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        if self.proxies:
            proxy = self.proxies[self.current_proxy_index % len(self.proxies)]
            self.current_proxy_index += 1
            
            request.meta['proxy'] = proxy
            spider.logger.info(f"Using proxy: {proxy}")
