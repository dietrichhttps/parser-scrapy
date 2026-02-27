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
    """Middleware to render JavaScript using Playwright with browser pool"""

    def __init__(self, crawler):
        self.crawler = crawler
        self.region = crawler.settings.get('REGION', 'Krasnodar')
        self.city_id = crawler.settings.get('CITY_ID', '117274')
        self.playwright = None
        self.browser = None
        self.browser_pool = []
        self.max_browsers = 2
        self.lock = asyncio.Lock()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    async def _get_browser(self):
        """Get a browser from pool or create new one"""
        async with self.lock:
            if self.browser_pool:
                return self.browser_pool.pop()
        
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
            ]
        )
        return browser

    async def _release_browser(self, browser):
        """Return browser to pool"""
        async with self.lock:
            if len(self.browser_pool) < self.max_browsers:
                self.browser_pool.append(browser)
            else:
                try:
                    await browser.close()
                except:
                    pass

    async def process_request(self, request, spider):
        browser = None
        context = None
        page = None
        
        try:
            browser = await self._get_browser()
            context = await browser.new_context()
            
            await context.add_cookies([
                {"name": "city", "value": self.city_id, "domain": "alkoteka.com", "path": "/"},
                {"name": "region", "value": "3", "domain": "alkoteka.com", "path": "/"},
            ])

            page = await context.new_page()

            await page.goto(request.url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(1500)
            
            if '/catalog/' in request.url:
                for _ in range(2):
                    try:
                        await page.evaluate('window.scrollBy(0, 1000)')
                        await page.wait_for_timeout(300)
                    except:
                        pass

            content = await page.content()
            
            return HtmlResponse(
                url=request.url,
                body=content,
                encoding='utf-8',
                request=request
            )
        except Exception as e:
            spider.logger.error(f"Playwright error: {e}")
            return None
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass
            if context:
                try:
                    await context.close()
                except:
                    pass
            if browser:
                await self._release_browser(browser)

    async def spider_closed(self):
        """Cleanup when spider closes"""
        async with self.lock:
            for browser in self.browser_pool:
                try:
                    await browser.close()
                except:
                    pass
            self.browser_pool.clear()
        
        if self.playwright:
            await self.playwright.stop()


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
