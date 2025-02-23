import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.http import HtmlResponse
import time
import re
import json

class EcommerceCrawler(CrawlSpider):
    """
    A Scrapy-based web crawler that discovers and lists product URLs 
    across multiple e-commerce websites.

    Features:
    - Detects various product URL patterns (e.g., /product/, /item/, /p/).
    - Handles dynamically loaded content with Selenium.
    - Saves discovered URLs in a structured JSON file.

    Attributes:
    - allowed_domains: List of domains to crawl.
    - start_urls: Initial URLs to begin crawling.
    - discovered_urls: Dictionary mapping domains to product URLs.
    """
    name = "ecommerce_crawler"
    allowed_domains = ["example.com"]  # Replace with actual domains
    start_urls = ["https://www.example.com"]  # Replace with actual URLs
    discovered_urls = {}

    rules = (
        Rule(LinkExtractor(allow=(r'/product/', r'/item/', r'/p/')), callback='parse_product', follow=True),
    )

    def __init__(self, *args, **kwargs):
        """
        Initializes the web crawler with Selenium for handling JavaScript-heavy pages.
        """
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)

    def parse_product(self, response):
        """
        Extracts product URLs and stores them in a structured format.

        Args:
            response (scrapy.http.Response): The response object containing the HTML page.

        Yields:
            dict: A dictionary containing the discovered product URL.
        """
        product_url = response.url
        domain = response.url.split("/")[2]
        if domain not in self.discovered_urls:
            self.discovered_urls[domain] = set()
        self.discovered_urls[domain].add(product_url)
        print(f"Discovered product URL: {product_url}")
        yield {"product_url": product_url}

    def parse(self, response):
        """
        Handles dynamically loaded content using Selenium.

        Args:
            response (scrapy.http.Response): The response object containing the HTML page.

        Yields:
            scrapy.Request: Requests to follow discovered product links.
        """
        self.driver.get(response.url)
        time.sleep(3)  # Wait for JS to load
        html = self.driver.page_source
        new_response = HtmlResponse(url=response.url, body=html, encoding='utf-8')

        links = new_response.xpath("//a/@href").getall()
        for link in links:
            if re.search(r'/product/|/item/|/p/', link):
                yield response.follow(link, callback=self.parse_product)

    def closed(self, reason):
        """
        Closes the Selenium WebDriver and saves discovered URLs to a JSON file.

        Args:
            reason (str): The reason why the spider was closed.
        """
        self.driver.quit()
        structured_output = {domain: list(urls) for domain, urls in self.discovered_urls.items()}
        with open("discovered_product_urls.json", "w") as f:
            json.dump(structured_output, f, indent=4)
