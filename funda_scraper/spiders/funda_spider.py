from base64 import urlsafe_b64decode
import re
from scrapy.spiders import Spider

class FundaSpider(Spider):
    name = 'funda_spider'

    def parse(self, response):
        for lstng in response.css(".search-result").getall():
            yield {'text': re.search('href=\"(.+?)\"', lstng).group(1)}

