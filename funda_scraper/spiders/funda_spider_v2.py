from fileinput import filename
import scrapy
from scrapyscript import Job, Processor
import re
import json
import webbrowser
import schedule
import time

class FundaSpider(scrapy.Spider):
    name = 'fundaspiderv2'

    def parse(self, response):
        for lstng in response.css(".search-result").getall():
            yield {'text': lstng}

def fill_listing_list(filename, spider):
    """Takes a spider and an empty .json filename and fills it with all listings currently available"""
    url_list = [link + str(i) for i in range(1,10) for link in \
        ['https://www.funda.nl/koop/gemeente-den-bosch/200000-400000/dakterras/tuin/sorteer-datum-af/p',
         'https://www.funda.nl/koop/gemeente-vught/200000-400000/dakterras/tuin/sorteer-datum-af/p',
         'https://www.funda.nl/koop/gemeente-sint-michielsgestel/200000-400000/dakterras/tuin/sorteer-datum-af/p']]

    FundaJob = Job(spider, start_urls = url_list)
    processor = Processor(settings=None)
    fetched_listings = processor.run(FundaJob)

    listings = []
    for listing in fetched_listings:
        listing_text = listing['text']
        href_string = re.search('href=\"(.+?)\"', listing_text)
        if href_string:
            grouped_href_string = href_string.group(1)
            listings.append(grouped_href_string)

    json_string = json.dumps(listings)
    with open(filename, 'w') as outfile:
        outfile.write(json_string)

def check_and_update_new_listings(filename, spider):
    url_list = ['https://www.funda.nl/koop/gemeente-den-bosch/200000-400000/dakterras/tuin/sorteer-datum-af/',
                'https://www.funda.nl/koop/gemeente-vught/200000-400000/dakterras/tuin/sorteer-datum-af/',
                'https://www.funda.nl/koop/gemeente-sint-michielsgestel/200000-400000/dakterras/tuin/sorteer-datum-af/']
    FundaJob = Job(spider, start_urls = url_list)
    processor = Processor(settings=None)
    fetched_listings = processor.run(FundaJob)

    f = open(filename)
    old_listings = json.load(f)
    f.close()

    listings = []
    for listing in fetched_listings:
        listing_text = listing['text']
        href_string = re.search('href=\"(.+?)\"', listing_text)
        if href_string:
            grouped_href_string = href_string.group(1)
            listings.append(grouped_href_string)

    print("#######################################\n###########checking listings###########\n#######################################")
    
    for listing in listings:
        if listing not in old_listings:
            print("adding new listing: ", listing)
            old_listings.append(listing)
            #base_html = "https://www.funda.nl"
            #webbrowser.open(base_html + listing)
    

    # f = open(filename)
    # f.seek(0) 
    # f.truncate(0) 
    # f.close()

    json_string = json.dumps(old_listings)
    with open(filename, 'w') as outfile:
        outfile.write(json_string)

def check_database_empty(filename):
    f = open(filename)
    old_listings = json.load(f)
    f.close()
    if not old_listings:
        return True
    else:
        return False


filename = "listing_database_v2.json"
spider = FundaSpider

if check_database_empty(filename):
    fill_listing_list(filename, spider)

schedule.every(10).seconds.do(check_and_update_new_listings,filename, spider)

while True:
    schedule.run_pending()
    time.sleep(1)