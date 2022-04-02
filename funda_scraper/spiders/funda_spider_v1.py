import scrapy
import re
from scrapy.crawler import CrawlerProcess
from scrapyscript import Job, Processor
from scrapy.spiders import Spider
from scrapy import Request
import json
import webbrowser
import schedule
import time

class FundaSpider(scrapy.Spider):
    name = 'fundaspiderv1'
    start_urls = ['https://www.funda.nl/koop/gemeente-den-bosch/200000-400000/dakterras/tuin/sorteer-datum-af/',
                  'https://www.funda.nl/koop/gemeente-vught/200000-400000/dakterras/tuin/sorteer-datum-af/']
    LOG_LEVEL = 'INFO'
    LOG_ENABLED = False

    def parse(self, response):
        for lstng in response.css(".search-result").getall():
            yield {
                'text': lstng
            }

def run_spider(spider):
    FundaJob = Job(spider)
    processor = Processor(settings=None)
    fetched_listings = processor.run(FundaJob)
    return fetched_listings

def load_listings_json(filename):
    f = open(filename)
    old_listings = json.load(f)
    f.close()
    return old_listings

def check_for_new_listing(spider_listings, old_listings):
    listings = []
    for listing in spider_listings:
        listing_text = listing['text']
        href_string = re.search('href=\"(.+?)\"', listing_text)
        if href_string:
            grouped_href_string = href_string.group(1)
            listings.append(grouped_href_string)

    print("#######################################")
    print("###########checking listings###########")
    print("#######################################")

    for listing in listings:
        if listing not in old_listings:
            print("adding new listing!!!: ", listing)
            old_listings.append(listing)
            base_html = "https://www.funda.nl"
            webbrowser.open(base_html + listing)
    
    return old_listings

def clear_and_write_json(filename, listings):
    f = open(filename, "r+") 
    f.seek(0) 
    f.truncate() 
    f.close()

    json_string = json.dumps(listings)
    with open(filename, 'w') as outfile:
        outfile.write(json_string)

def complete_check():
    filename = 'listing_database.json'

    fetched_listings = run_spider(FundaSpider)
    old_listings = load_listings_json(filename)
    complete_listings = check_for_new_listing(fetched_listings, old_listings)
    clear_and_write_json(filename, complete_listings)

complete_check()

# if __name__ == "__main__":
#     schedule.every(15).minutes.do(complete_check)
#     while True:
#         schedule.run_pending()
#         time.sleep(1)