from base64 import urlsafe_b64decode
import re
from scrapyscript import Job, Processor
from scrapy.spiders import Spider
import json
import webbrowser
import schedule
import time

######## SCRAPY SPIDER FUNCTIONS #######
class FundaSpider(Spider):
    name = 'fundaspiderv2'

    def parse(self, response):
        for lstng in response.css(".search-result").getall():
            yield {'text': re.search('href=\"(.+?)\"', lstng).group(1)}

def run_spider(spider, url_list):
    funda_job = Job(spider, start_urls = url_list)
    processor = Processor(settings=None)
    fetched_listings = processor.run(funda_job)
    return fetched_listings

############ JSON FUNCTIONS ############
def clear_json(filename):
   f = open(filename, "r+")
   f.seek(0)
   f.truncate()
   f.close()

def write_json(filename, listings):
   json_string = json.dumps(listings)
   with open(filename, 'w') as outfile:
       outfile.write(json_string)

def read_json(filename):
    f = open(filename)
    saved_listings = json.load(f)
    f.close()
    return saved_listings

##### LISTING COMPARISON FUNCTIONS #####
def check_new_listings(spider_output, all_listings, open_link=True):
    for lstng in spider_output:
        listing = lstng['text']
        if listing not in all_listings:
            print("adding new listing!!!: ", listing)
            all_listings.append(listing)
            base_html = "https://www.funda.nl"
            if open_link:
                webbrowser.open(base_html + listing)
  
    return all_listings


def periodic_checker(database, url_list):
    saved_listings = read_json(database)

    # Check if database is empty. fill without opening links if so
    open_links = False if not saved_listings else True

    # Run spider and check for new listings
    fetched_listings = run_spider(FundaSpider, url_list)
    all_listings = check_new_listings(fetched_listings, saved_listings, open_links)

    # Clear database and write new complete list of listings
    clear_json(database)
    write_json(database, all_listings)


############### VARIABLES ##############
one_loop = True
database = "listing_database.json"
url_list = ['https://www.funda.nl/koop/gemeente-den-bosch/200000-400000/dakterras/tuin/sorteer-datum-af/',
            'https://www.funda.nl/koop/gemeente-vught/200000-400000/dakterras/tuin/sorteer-datum-af/']

############## MAIN LOOP ###############
if __name__ == "__main__":

    if one_loop:
        periodic_checker(database, url_list)
    else:
        schedule.every(15).minutes.do(periodic_checker, database = database, url_list = url_list)

    while True:
        schedule.run_pending()
        time.sleep(1)