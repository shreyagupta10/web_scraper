import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.http import HtmlResponse
import time
import re
import json

class EcommerceCrawler(CrawlSpider):
    name = "ecommerce_crawler"
    allowed_domains = ["amazon.com"]  # Replace with actual domains
    start_urls = ["https://www.amazon.com"]  # Replace with actual URLs
    discovered_urls = {}

    # Define rules to follow links matching product patterns
    rules = (
        Rule(LinkExtractor(allow=(r'/product/', r'/item/', r'/p/')), callback='parse_product', follow=True),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)

    def parse_product(self, response):
        product_url = response.url
        domain = response.url.split("/")[2]
        if domain not in self.discovered_urls:
            self.discovered_urls[domain] = set()
        self.discovered_urls[domain].add(product_url)
        print(f"Discovered product URL: {product_url}")
        yield {"product_url": product_url}

    def parse(self, response):
        """ Handle dynamic content using Selenium for JavaScript-heavy pages. """
        self.driver.get(response.url)
        time.sleep(3)  # Wait for JS to load
        html = self.driver.page_source
        new_response = HtmlResponse(url=response.url, body=html, encoding='utf-8')

        # Extract URLs manually if needed
        links = new_response.xpath("//a/@href").getall()
        for link in links:
            if re.search(r'/product/|/item/|/p/', link):
                yield response.follow(link, callback=self.parse_product)

    def closed(self, reason):
        self.driver.quit()
        # Save discovered URLs to a JSON file
        structured_output = {domain: list(urls) for domain, urls in self.discovered_urls.items()}
        with open("discovered_product_urls.json", "w") as f:
            json.dump(structured_output, f, indent=4)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(EcommerceCrawler)
    process.start()
