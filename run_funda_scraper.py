from funda_scraper.spiders.funda_spider import FundaSpider
import config

from scrapyscript import Job, Processor
import json, requests
import webbrowser
import schedule, time

############ JSON FUNCTIONS ############
def write_json(filename, listings):
    '''function write dictionaries to jsonl file, overwrites current data'''
    with open(filename, 'w') as outfile:
        for entry in listings:
            json.dump(entry, outfile)
            outfile.write('\n')

def read_json(filename):
    '''function to read jsonl file and turn to dictionaries'''
    # read data and add to list
    with open(filename, 'r') as json_file:
        json_list = list(json_file)

    # turn items in list to dictionaries
    saved_listings = []
    for json_str in json_list:
        result = json.loads(json_str)
        saved_listings.append(result)
    return saved_listings

###### PUSH NOTIFICATION FUNCTION ######
def pushbullet_notification(title, body, token):
    '''function to send notification to pushbullet app'''
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
    '''function to compare spider output to listings in database and detect new ones'''
    # make list of adressnames 
    all_listing_names = [x['street_name'] for x in all_listings]
    new_listings = []

    # loop over listings and check if in database
    for lstng in spider_output:
        listing = lstng['street_name']
        if listing not in all_listing_names:

            # append new listings to complete database and separate list
            print("adding new listing!!!: ", listing)
            all_listings.append(lstng)
            new_listings.append(lstng)
  
    return all_listings, new_listings

######## SCRAPY SPIDER FUNCTIONS #######
def run_spider(spider, url_list):
    '''function to run a spider job and return dictionaries in list'''
    funda_job = Job(spider, start_urls = url_list)
    processor = Processor(settings=None)
    fetched_listings = processor.run(funda_job)
    return [dict(x) for x in fetched_listings]

############ MAIN FUNCTION #############
def periodic_checker(database, url_list, token, send_notification, open_links):
    '''main function to run spider and send notification if new listing is found'''
    saved_listings = read_json(database)

    # overwrite if database is empty.
    open_links = False if not saved_listings else open_links
    send_notification = False if not saved_listings else send_notification

    # Run spider and check for new listings
    fetched_listings = run_spider(FundaSpider, url_list)
    all_listings, new_listings = check_new_listings(fetched_listings, saved_listings)

    # loop over new listings and send notification and/or open in webbrowser
    for listing in new_listings:
        if send_notification:
            current_time = time.strftime("%H:%M", time.localtime())
            title = "[{}] {}".format(current_time, listing['street_name'])
            body = "{}\nvraagprijs: €{}.-\n{}m²/{}m² - {} kamers\n\n{}".format(listing['postal_code'], listing['price'],
                                                                    listing['living_space'], listing['plot_size'],
                                                                    listing['nr_of_rooms'], listing['url'])
            pushbullet_notification(title, body, token)
        if open_links:
            webbrowser.open(listing['url'])

    # write new list of listings if new listing(s) found
    write_json(database, all_listings)

############### VARIABLES ##############
one_loop =          config.ONE_LOOP
open_links =        config.OPEN_LINKS
send_notification = config.SEND_NOTIFICATION
database =          config.DATABASE
url_list =          config.URL_LIST
token =             config.PUSHBULLET_TOKEN

############## MAIN LOOP ###############
if __name__ == "__main__":

    if one_loop:
        periodic_checker(database, url_list, token, send_notification, open_links)
    else:
        schedule.every(15).minutes.do(periodic_checker, database = database, url_list = url_list, 
                                                        token = token, send_notification=send_notification, 
                                                        open_links=open_links)
        while True:
            schedule.run_pending()
            time.sleep(1)