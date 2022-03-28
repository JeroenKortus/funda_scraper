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

class FundaSpider(Spider):

    name = 'fundaspiderv3'

    def parse(self, response):
        for lstng in response.css(".search-result").getall():
            yield {'text': re.search('href=\"(.+?)\"', lstng).group(1)}

def clear_json(filename):
   f = open(filename, "r+")
   f.seek(0)
   f.truncate()
   f.close()

def write_json(filename, listings):
   json_string = json.dumps(listings)
   with open(filename, 'w') as outfile:
       outfile.write(json_string)

def check_new_listings(spider_output, old_listings):
    for listing in spider_output:
        if listing not in old_listings:
            print("adding new listing!!!: ", listing)
            old_listings.append(listing)
            base_html = "https://www.funda.nl"
            webbrowser.open(base_html + listing)
  
    return old_listings


def periodic_checker():
    return

database = "listing_database.json"

if __name__ == "__main__":
    
    clear_json(database)

    schedule.every(15).minutes.do(periodic_checker)

    while True:
        schedule.run_pending()
        time.sleep(1)