# Funda scraper

This repo contains a simple Funda scraper I build using scrapy to notify me within minutes when new listing are added with my criteria.

## Installation

Clone the github to your own machine. Make sure the machine has Python ```3.9.10``` and pip installed.

```bash
git clone https://github.com/JeroenKortus/funda_scraper.git
```

Install all packages used in this 

```bash
pip install requirements.txt
```
To setup pushbullet to receive notifications follow this [geeksforgeeks](https://www.geeksforgeeks.org/python-web-app-to-send-push-notification-to-your-phone/) tutorial. To give you a quick overview of the simple steps:

On PC:
- Go to Pushbullet.com
- Create an account

On phone:
- Install the Pushbullet app on your phone.
- Log in using the same email address that you used to log in to your PC.

On PC:
- Go to Pushbullet and obtain the access token.

This access token is what you will need to send messages using Python.

Next, go to Funda and enter your search criteria and press search. This should navigate you to a webpage with listings. Sort the webpage on newest listings and copy the url. The url should look something like this:
```
https://www.funda.nl/koop/gemeente-den-bosch/200000-400000/dakterras/tuin/sorteer-datum-af/
```

The last step is to edit the config file to your own liking. something like this:

```python
ONE_LOOP = False
OPEN_LINKS = True
SEND_NOTIFICATION = True
DATABASE = "listing_database.jsonl"
URL_LIST = ['https://www.funda.nl/koop/gemeente-den-bosch/200000-400000/dakterras/tuin/sorteer-datum-af/',
            'https://www.funda.nl/koop/gemeente-vught/200000-400000/dakterras/tuin/sorteer-datum-af/']
PUSHBULLET_TOKEN = "string_of_your_token"
```


## Usage
Navigate to the folder containing the ```run_funda_scraper``` file and run it.
```bash
python run_funda_scraper.py
```


## License
[MIT](https://choosealicense.com/licenses/mit/)