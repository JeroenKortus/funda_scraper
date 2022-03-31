from base64 import urlsafe_b64decode
import re
from scrapyscript import Job, Processor
from scrapy.spiders import Spider
import json
import webbrowser
import schedule
import time
import requests

import sys
sys.path.insert(0, '/Users/jk/data_science/funda_scraper/')
import config

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

###### PUSH NOTIFICATION FUNCTION ######
def pushbullet_noti(title, body, token):

    # Make a dictionary that includes, title and body
    msg = {"type": "note", "title": title, "body": body}

    # Sent a posts request
    resp = requests.post('https://api.pushbullet.com/v2/pushes',
                         data=json.dumps(msg),
                         headers={'Authorization': 'Bearer ' + token,
                                  'Content-Type': 'application/json'})

    if resp.status_code != 200:  # Check if fort message send with the help of status code
        raise Exception('Error', resp.status_code)
    else:
        print('Message sent!')

###### LISTING COMPARISON FUNCTION #####
def check_new_listings(spider_output, all_listings):
    new_listings = []
    for lstng in spider_output:
        listing = lstng['text']
        if listing not in all_listings:
            print("adding new listing!!!: ", listing)
            all_listings.append(listing)
            base_html = "https://www.funda.nl"
            new_listings.append(base_html + listing)
  
    return all_listings, new_listings

############ MAIN FUNCTION #############
def periodic_checker(database, url_list, token, open_links):
    saved_listings = read_json(database)

    # overwrtie if database is empty.
    open_links = False if not saved_listings else open_links

    # Run spider and check for new listings
    fetched_listings = run_spider(FundaSpider, url_list)
    all_listings, new_listings = check_new_listings(fetched_listings, saved_listings)

    for listing in new_listings:
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        pushbullet_noti("New listing found! ({})".format(current_time), listing, token)
        if open_links:
            webbrowser.open(listing)

    # Clear database and write new complete list of listings
    clear_json(database)
    write_json(database, all_listings)

############### VARIABLES ##############
one_loop = False
open_links = False
database = "listing_database.json"
url_list = ['https://www.funda.nl/koop/gemeente-den-bosch/200000-400000/dakterras/tuin/sorteer-datum-af/',
            'https://www.funda.nl/koop/gemeente-vught/200000-400000/dakterras/tuin/sorteer-datum-af/']
token = config.PUSHBULLET_TOKEN

############## MAIN LOOP ###############
if __name__ == "__main__":

    if one_loop:
        periodic_checker(database, url_list, token)
    else:
        schedule.every(15).minutes.do(periodic_checker, database = database, url_list = url_list, token = token)

        while True:
            schedule.run_pending()
            time.sleep(1)