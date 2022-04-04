from scrapy.spiders import Spider
from scrapy.loader import ItemLoader
from funda_scraper.items import FundaScraperItem

# define spider
class FundaSpider(Spider):

    name = 'funda_spider'

    def parse(self, response):

        # make spider get search-result from webpages
        listings = response.css('li.search-result')
        for lstng in listings:

            # initiate item loader for spider output
            loader = ItemLoader(item=FundaScraperItem(), selector=lstng)
            
            # add relevant items to loader
            loader.add_css('street_name', '.search-result__header-title.fd-m-none::text')
            loader.add_css('postal_code', '.search-result__header-subtitle.fd-m-none::text')
            loader.add_css('price', '.search-result-price::text')
            loader.add_css('living_space', 'ul.search-result-kenmerken span ::text')
            loader.add_css('plot_size', 'ul.search-result-kenmerken span ::text')
            loader.add_css('nr_of_rooms', 'ul.search-result-kenmerken li ::text')
            loader.add_css('url', 'div.search-result__header-title-col a::attr(href)')
            
            # yield result
            yield loader.load_item()