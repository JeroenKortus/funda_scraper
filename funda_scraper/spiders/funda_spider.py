from base64 import urlsafe_b64decode
import re
from scrapy.spiders import Spider

class FundaSpider(Spider):
    name = 'funda_spider'

    def parse(self, response):
        listings = response.css(".search-result").getall()
        for lstng in listings:
            yield {'text': re.search('href=\"(.+?)\"', lstng).group(1)}
            #'street_name': lstng.css(".search-result__header-title.fd-m-none::text").getall() - pp remove \r\n
            #'postal_code': lstng.css(".search-result__header-subtitle.fd-m-none::text").getall() - pp remove \r\n
            #'price': lstng.css(".search-result-price::text").get() - pp turn into int
            #'living_space': lstng.css("ul.search-result-kenmerken span ::text").get()
            #'plot_size': lstng.css("ul.search-result-kenmerken span ::text").getall() - pp get [1]
            #'nr_of_rooms': lstng.css("ul.search-result-kenmerken li ::text").getall() - pp get [-1]
            #'url': lstng.css("div.search-result__header-title-col a::attr(href)").get() - pp add base url
