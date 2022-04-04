from scrapy.item import Item, Field
from scrapy.loader.processors import MapCompose, TakeFirst
import re

def clean_and_strip(text):
    '''function to remove \r\n and strip leading and trailing spaces'''
    text = text.replace("\r\n","").strip()
    return text

def keep_ints(text):
    '''function to remove all except numbers'''
    text = re.sub("[^0-9]", "", text)
    return text

def complete_url(text):
    '''function to add base url to listing href'''
    return "https://www.funda.nl" + text

class TakeLast:
    '''class to take last item from returned list'''
    def __call__(self, values):
        return values[-1]

class FundaScraperItem(Item):
    '''item for processing and structuring returned components'''
    street_name = Field(
        input_processor=MapCompose(clean_and_strip),
        output_processor=TakeFirst()
    )
    postal_code = Field(
        input_processor=MapCompose(clean_and_strip),
        output_processor=TakeFirst()
    )
    price = Field(
        input_processor=MapCompose(keep_ints),
        output_processor=TakeFirst()
    )
    living_space = Field(
        input_processor=MapCompose(keep_ints),
        output_processor=TakeFirst()
    )
    plot_size = Field(
        input_processor=MapCompose(keep_ints),
        output_processor=TakeLast()
    )
    nr_of_rooms = Field(
        input_processor=MapCompose(keep_ints),
        output_processor=TakeLast()
    )
    url = Field(
        input_processor=MapCompose(complete_url),
        output_processor=TakeFirst()
    )