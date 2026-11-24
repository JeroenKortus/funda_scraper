import json
import webbrowser
import schedule, time
from datetime import datetime
import os

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time as time_module

# Notion imports
from notion_client import Client

# iPhone notification imports
import requests



############ NOTION CONFIGURATION ############
try:
    from config import NOTION_TOKEN, NOTION_DATABASE_ID
except ImportError:
    print("⚠️  config.py not found or not configured. Notion integration disabled.")
    NOTION_TOKEN = 'your_notion_token_here'
    NOTION_DATABASE_ID = 'your_database_id_here'

# Initialize Notion client
notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN != 'your_notion_token_here' else None

############ PUSHOVER CONFIGURATION ############
try:
    from config import PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN
    pushover_configured = True
except ImportError:
    print("⚠️  Pushover credentials not found in config.py. iPhone notifications disabled.")
    PUSHOVER_USER_KEY = None
    PUSHOVER_API_TOKEN = None
    pushover_configured = False

############ JSON FUNCTIONS ############
def write_json(filename, listings):
    '''function write dictionaries to jsonl file, overwrites current data'''
    with open(filename, 'w') as outfile:
        for entry in listings:
            json.dump(entry, outfile)
            outfile.write('\n')

def read_json(filename):
    '''function to read jsonl file and turn to dictionaries'''
    try:
        with open(filename, 'r') as json_file:
            json_list = list(json_file)

        saved_listings = []
        for json_str in json_list:
            result = json.loads(json_str)
            saved_listings.append(result)
        return saved_listings
    except FileNotFoundError:
                return []

############ IPHONE NOTIFICATION FUNCTIONS ############
def send_iphone_notification(listing_count, listings):
    '''Send push notification to iPhone via Pushover API'''
    if not pushover_configured or not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        return False
    
    try:
        if listing_count == 1:
            listing_name = listings[0].get('street_name', 'Unknown')
            title = "🏠 Nieuwe woning gevonden!"
            message = f"{listing_name}\n\nKlik om te bekijken op Funda!"
            url = f"https://www.funda.nl{listings[0].get('url', '')}" if not listings[0].get('url', '').startswith('http') else listings[0].get('url', '')
        else:
            title = f"🏠 {listing_count} nieuwe woningen!"
            listing_names = [lst.get('street_name', 'Unknown') for lst in listings[:3]]
            message = "\n".join([f"• {name}" for name in listing_names])
            if listing_count > 3:
                message += f"\n... en nog {listing_count - 3} meer!"
            url = "https://www.funda.nl/zoeken/koop?selected_area=[%22den-bosch%22]&price=%220-400000%22&object_type=[%22apartment%22]"
        
        # Send the push notification via Pushover API
        response = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message,
            "url": url,
            "url_title": "Bekijk op Funda",
            "sound": "magic",  # iPhone notification sound
            "priority": 1  # High priority to bypass quiet hours
        })
        
        if response.status_code == 200:
            print(f"📱 Notification sent")
            return True
        else:
            print(f"❌ Notification failed: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Notification error: {e}")
        return False

############ NOTION FUNCTIONS ############
def add_listing_to_notion(listing):
    '''Add a new listing to Notion database'''
    if not notion or NOTION_DATABASE_ID == 'your_database_id_here':
        return False
    
    try:
        # Convert found_date string to proper date format for Notion
        found_date = datetime.strptime(listing['found_date'], '%Y-%m-%d %H:%M:%S')
        
        # Create the page in Notion
        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": listing.get('street_name', 'Unknown')
                            }
                        }
                    ]
                },
                "URL": {
                    "url": f"https://www.funda.nl{listing.get('url', '')}" if not listing.get('url', '').startswith('http') else listing.get('url', '')
                },
                "Datum gevonden": {
                    "date": {
                        "start": found_date.strftime('%Y-%m-%d')
                    }
                },
                "Status": {
                    "status": {
                        "name": "Nieuw!"
                    }
                }
            }
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Notion error: {e}")
        return False

###### JSON EXTRACTION FUNCTION #######
def extract_listings_from_json(page_source):
    '''Extract listings data from the JSON in Nuxt.js page'''
    import re
    import json
    
    try:
        # Look for the JSON data in the page
        json_pattern = r'data-nuxt-data="nuxt-app"[^>]*id="__NUXT_DATA__"[^>]*>([^<]+)</script>'
        match = re.search(json_pattern, page_source)
        
        if not match:
            # Try alternative patterns
            alt_patterns = [
                r'<script[^>]*id="__NUXT_DATA__"[^>]*>([^<]+)</script>',
                r'window\.__NUXT__\s*=\s*({.+?});',
                r'__NUXT_DATA__[^>]*>([^<]+)<',
            ]
            
            for i, pattern in enumerate(alt_patterns):
                match = re.search(pattern, page_source, re.DOTALL)
                if match:
                    break
            
            if not match:
                print("❌ No listing data found")
                return []
        
        json_str = match.group(1)
        
        # Parse the JSON structure
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"❌ Data parsing failed: {e}")
            return []
        
        # Navigate through the Nuxt.js serialized state
        listings = []
        
        # Look for listings reference (should be around index 2170 based on debug output)
        if isinstance(data, list) and len(data) > 2170:
            listings_data = data[2170]  # This should be the listings array
            
            if isinstance(listings_data, list):
                for i, listing_ref in enumerate(listings_data):
                    try:
                        if isinstance(listing_ref, int) and listing_ref < len(data):
                            listing_obj = data[listing_ref]
                            
                            # Handle nested references like ['Reactive', 2172]
                            if isinstance(listing_obj, list) and len(listing_obj) >= 2:
                                if isinstance(listing_obj[1], int) and listing_obj[1] < len(data):
                                    actual_listing = data[listing_obj[1]]
                                    listing_obj = actual_listing
                            
                            if isinstance(listing_obj, dict):
                                # Look for URL and address information
                                url = None
                                street_name = "Unknown"
                                
                                # Try to find URL in the listing object
                                for key, value in listing_obj.items():
                                    if isinstance(value, str):
                                        if '/detail/' in value:
                                            url = value
                                        elif any(word in key.lower() for word in ['address', 'street', 'name', 'title']):
                                            street_name = value
                                    elif isinstance(value, int) and value < len(data):
                                        # Check if this reference contains URL or address info
                                        ref_obj = data[value]
                                        if isinstance(ref_obj, str):
                                            if '/detail/' in ref_obj:
                                                url = ref_obj
                                            elif any(word in key.lower() for word in ['address', 'street', 'name', 'title']):
                                                street_name = ref_obj
                                
                                if url:
                                    listing = {
                                        'street_name': street_name,
                                        'url': url,
                                        'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    listings.append(listing)
                    
                    except (IndexError, TypeError) as e:
                        continue  # Skip invalid entries
        
        # If no listings found with the first approach, try searching the entire JSON
        if not listings:
            # Convert the entire JSON to string and search for URL patterns
            full_json_str = json.dumps(data)
            
            # Look for Funda detail URLs with multiple patterns
            url_patterns = [
                r'/detail/koop/[^"\'\\,\]]+',  # Standard detail URLs
                r'detail/koop/[^"\'\\,\]]+',   # Without leading slash
                r'/koop/[^/]+/appartement-[^"\'\\,\]]+',  # Alternative format
                r'appartement-[^/]+/\d+',      # Just the appartement part
            ]
            
            all_found_urls = []
            
            for pattern_idx, pattern in enumerate(url_patterns):
                urls = re.findall(pattern, full_json_str)
                if urls:
                    for url in urls:
                        if not url.startswith('/'):
                            url = '/' + url
                        
                        # Clean up the URL
                        if url not in all_found_urls:
                            all_found_urls.append(url)
            
            # Process found URLs
            if all_found_urls:
                # Deduplicate by listing ID (the number at the end of URLs)
                seen_ids = set()
                
                for url in all_found_urls:
                    # Extract listing ID from URL
                    listing_id = None
                    id_match = re.search(r'/(\d+)/?$', url)
                    if id_match:
                        listing_id = id_match.group(1)
                    
                    # Skip if we've already processed this listing ID
                    if listing_id and listing_id in seen_ids:
                        continue
                    
                    if listing_id:
                        seen_ids.add(listing_id)
                    
                    # Extract street name from URL
                    parts = url.split('/')
                    street_name = "Unknown"
                    
                    for part in parts:
                        if 'appartement-' in part:
                            street_part = part.replace('appartement-', '').replace('-', ' ')
                            # Remove trailing numbers/IDs
                            street_name = re.sub(r'/\d+$', '', street_part).strip().title()
                            break
                    
                    # Ensure URL starts with /detail/ for consistency
                    if not url.startswith('/detail/'):
                        if url.startswith('/koop/'):
                            url = url.replace('/koop/', '/detail/koop/')
                        elif url.startswith('/appartement-'):
                            url = '/detail/koop/den-bosch' + url
                    
                    listing = {
                        'street_name': street_name,
                        'url': url,
                        'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    listings.append(listing)
        
        return listings
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return []

###### SELENIUM SCRAPER FUNCTION #######
def scrape_funda_with_selenium(url):
    '''function to scrape Funda using Selenium to handle JavaScript'''
    
    print(f"🌐 Scraping listings...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    # Setup Chrome driver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e2:
            print(f"❌ Browser setup failed: {e2}")
            return []
    
    try:
        driver.get(url)
        
        # Wait for JavaScript to render the listings
        time_module.sleep(20)
        
        # Extract data from the JSON
        page_source = driver.page_source
        
        listings = extract_listings_from_json(page_source)
        
        return listings
        
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return []
    
    finally:
        driver.quit()

###### LISTING COMPARISON FUNCTION #####
def check_new_listings(spider_output, all_listings):
    '''function to compare spider output to listings in database and detect new ones'''
    
    # Get existing listing names
    all_listing_names = []
    for x in all_listings:
        if isinstance(x, dict):
            street_name = x.get('street_name', 'Unknown')
            if isinstance(street_name, list) and street_name:
                all_listing_names.append(street_name[0])
            else:
                all_listing_names.append(street_name)
    
    new_listings = []

    # Check each listing against database
    for lstng in spider_output:
        if isinstance(lstng.get('street_name'), list) and lstng.get('street_name'):
            listing_name = lstng['street_name'][0]
        else:
            listing_name = lstng.get('street_name', 'Unknown')
            
        if listing_name not in all_listing_names:
            all_listings.append(lstng)
            new_listings.append(lstng)
  
    return all_listings, new_listings

############ MAIN FUNCTION #############
def periodic_checker(database, url_list):
    '''main function to run spider and send notification if new listing is found'''
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🔍 [{current_time}] Checking for new listings...")
    
    saved_listings = read_json(database)

    # Use Selenium scraper for JavaScript content
    fetched_listings = []
    for url in url_list:
        listings = scrape_funda_with_selenium(url)
        fetched_listings.extend(listings)
    
    all_listings, new_listings = check_new_listings(fetched_listings, saved_listings)

    # Process new listings
    for listing in new_listings:
        listing_name = listing.get('street_name', 'Unknown')
        if isinstance(listing_name, list) and listing_name:
            listing_name = listing_name[0]
        
        listing_url = listing.get('url', '')
        if isinstance(listing_url, list) and listing_url:
            listing_url = listing_url[0]
        
        print(f"🏠 New: {listing_name}")
        
        # Add to Notion
        if add_to_notion:
            add_listing_to_notion(listing)
        
        # Open in browser
        if open_in_browser:
            if isinstance(listing_url, str) and listing_url:
                if listing_url.startswith('http'):
                    webbrowser.open(listing_url)
                else:
                    webbrowser.open(f"https://www.funda.nl{listing_url}")

    # Save updated listings if new ones found
    if new_listings:
        write_json(database, all_listings)
        print(f"✅ Found {len(new_listings)} new listing{'s' if len(new_listings) > 1 else ''}!")
        
        # Send iPhone notification
        send_iphone_notification(len(new_listings), new_listings)
    else:
        print("📭 No new listings found")
    
    print(f"✅ [{current_time}] Check completed\n")

############### VARIABLES ##############
add_to_notion = True
open_in_browser = True 
one_loop = False
database = "listing_database.jsonl"
url_list = ['https://www.funda.nl/zoeken/koop?selected_area=[%22den-bosch/aawijk-noord%22,%22den-bosch/aawijk-zuid%22,%22den-bosch/bazeldonk%22,%22den-bosch/binnenstad-centrum%22,%22den-bosch/binnenstad-noord%22,%22den-bosch/binnenstad-oost%22,%22den-bosch/boschveld%22,%22den-bosch/de-bossche-pad%22,%22den-bosch/de-gestelse-buurt%22,%22den-bosch/de-hinthamerpoort%22,%22den-bosch/de-hofstad%22,%22den-bosch/de-meerendonk%22,%22den-bosch/de-muntel%22,%22den-bosch/de-vliert%22,%22den-bosch/deuteren%22,%22den-bosch/ertveld%22,%22den-bosch/graafsebuurt-noord%22,%22den-bosch/graafsebuurt-zuid%22,%22den-bosch/grevelingen%22,%22den-bosch/het-zand%22,%22den-bosch/orthen%22,%22den-bosch/orthen-west%22,%22den-bosch/orthenpoort%22,%22den-bosch/paleiskwartier%22,%22den-bosch/pettelaarpark%22,%22den-bosch/veemarktkwartier%22,%22den-bosch/vughterpoort%22,%22den-bosch/zuid%22,%22den-bosch/hintham-zuid%22,%22den-bosch/hintham-noord%22]&price=%220-400000%22&object_type=[%22apartment%22]&availability=[%22available%22]&floor_area=%2265-%22&sort=%22date_down%22']

############## MAIN LOOP ###############
def print_startup_message():
    '''Print a nice startup message with configuration info'''
    print("=" * 50)
    print("🏠 FUNDA SCRAPER STARTED")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target area: Den Bosch (29 neighborhoods)")
    print(f"💰 Price range: €0 - €400,000")
    print(f"📐 Min size: 65m²")
    print(f"🏠 Type: Apartments only")
    print(f"📝 Notion integration: {'✅ Enabled' if add_to_notion else '❌ Disabled'}")
    print(f"🌐 Browser opening: {'✅ Enabled' if open_in_browser else '❌ Disabled'}")
    print(f"📱 iPhone notifications: {'✅ Enabled' if pushover_configured else '❌ Disabled'}")
    
    if one_loop:
        print(f"🔄 Mode: Single run")
    else:
        print(f"🔄 Mode: Continuous (every 5 minutes)")
        print(f"⏰ Next check: {(datetime.now() + __import__('datetime').timedelta(minutes=5)).strftime('%H:%M:%S')}")

    print("=" * 50)

if __name__ == "__main__":
    print_startup_message()
    
    if one_loop:
        periodic_checker(database, url_list)
    else:
        schedule.every(5).minutes.do(periodic_checker, database=database, url_list=url_list)
        print(f"⏱️  Scheduler started - checking every 5 minutes...")
        print(f"💡 Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n🛑 Scraper stopped by user at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
