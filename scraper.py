import scrapy 
from scrapy.spiders import CrawlSpider
from scrapy.crawler import CrawlerProcess 
from itemloaders.processors import TakeFirst
from scrapy import Request 
from re import findall,sub 
from scrapy.http.response.html import HtmlResponse
from typing import List  
import json 
from scrapy.http.response.text import TextResponse
from scrapy.shell import inspect_response
from scrapy.loader import ItemLoader 
import pickle 

# part related to executable :
def warn_on_generator_with_return_value_stub(spider, callable):
    pass

scrapy.utils.misc.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub
scrapy.core.scraper.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub
#---------------------------------------------------------------------------------------------------#


class DetailsItem(scrapy.Item):
    short_address = scrapy.Field(
        output_processor=TakeFirst()
    )
    city = scrapy.Field(
        output_processor=TakeFirst()
    )
    state = scrapy.Field(
        output_processor=TakeFirst()
    )
    zip = scrapy.Field(
        output_processor=TakeFirst()
    )
    listed_by_company = scrapy.Field(
        output_processor=TakeFirst()
    )
    listed_by_agent_name = scrapy.Field(
        output_processor=TakeFirst()
    )
    property_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    virtual_tour_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    # page = scrapy.Field(
    #     output_processor=TakeFirst()
    # )
    # city_id = scrapy.Field(
    #     output_processor=TakeFirst()
    # )

class InfosSpider(scrapy.Spider):
    name = 'extractor'  
    state_template = 'https://www.remax.com/homes-for-sale/{state}'
    #popular_city_filters = '?filters={%22bPropertyType%22:[%22Single%20Family%22,%22Condo%22,%22Townhome%22],%22State%22:[%22FL%22],%22bStatus%22:[%22For%20Sale%22],%22hasVirtualTour%22:1}'
    #popular_city_filters = '?filters={%22bPropertyType%22:[%22Single%20Family%22,%22Condo%22,%22Townhome%22],%22State%22:[%22FL%22],%22bStatus%22:[%22For%20Sale%22],"openHouseOffset":"0",%22hasVirtualTour%22:1}'
    popular_city_filters = '?filters={{"bPropertyType":["Single%20Family","Condo","Townhome"],"bStatus":["For%20Sale"],"city":["{city}"],"openHouseOffset":"0","hasVirtualTour":1}}'
    states = {
        'AL': 'Alabama',
        'AK': 'Alaska',
        'AZ': 'Arizona',
        'AR': 'Arkansas',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'HI': 'Hawaii',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'IA': 'Iowa',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'ME': 'Maine',
        'MD': 'Maryland',
        'MA': 'Massachusetts',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MS': 'Mississippi',
        'MO': 'Missouri',
        'MT': 'Montana',
        'NE': 'Nebraska',
        'NV': 'Nevada',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NY': 'New York',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VT': 'Vermont',
        'VA': 'Virginia',
        'WA': 'Washington',
        'WV': 'West Virginia',
        'WI': 'Wisconsin',
        'WY': 'Wyoming',
    }

    def __init__(self,listing_url):
        self.listing_url = listing_url 

    # def start_requests(self):
    #     for state,state_2_char in self.states.items() :
    #         yield Request(
    #             self.state_template.format(state=state_2_char),
    #             callback=self.parse_state_popular_city,
    #             meta={
    #                 'state':state
    #             }
    #         )

    def start_requests(self):
        yield Request(
            self.listing_url + self.popular_city_filters.format(
                city=self.get_city_filter_name()
            ),
            callback=self.parse_total_pages,
            meta={
                'city_url':self.listing_url
            }
        )

    # def parse_state_popular_city(self,response):
    #     cities_ids = response.xpath('//div[@class="cat-table-row"]//a/@href').re('\d+$')
    #     cities_urls = [response.urljoin(url) for url in response.xpath('//div[@class="cat-table-row"]//a/@href').getall()]
    #     for city_id,city_url in zip(cities_ids,cities_urls) :
    #         yield Request(
    #             city_url + self.popular_city_filters,
    #             callback=self.parse_total_pages,
    #             meta={
    #                 'city_id':city_id,
    #                 #'state':response.meta['state'],
    #                 'city_url':city_url
    #             }
    #         )

    def parse_total_pages(self,response):
        properties_urls = [response.urljoin(url) for url in response.xpath('//div[@class="card-full-address cursor-pointer"]/a/@href').getall()]
        for url in properties_urls :
            yield Request(
                url,
                callback=self.parse_property,
                meta=response.meta
            )
        try : 
            total_pages = self.get_total_pages(response)
        except ValueError : 
            return 
        for page in range(2,total_pages+1):
            response.meta['page'] = page 
            yield Request(
                response.meta['city_url'] + f'/page-{page}' + self.popular_city_filters.format(
                city=self.get_city_filter_name()
            ),
                callback=self.parse_listing,
                dont_filter=True,
                meta=response.meta
            )

    def parse_listing(self,response):
        properties_urls = [response.urljoin(url) for url in response.xpath('//div[@class="card-full-address cursor-pointer"]/a/@href').getall()]
        for url in properties_urls :
            yield Request(
                url,
                callback=self.parse_property,
                dont_filter=True,
                meta=response.meta
            )

    def parse_property(self,response):
        loader = ItemLoader(DetailsItem(),response)
        loader.add_value('property_url',response.url)
        loader.add_xpath('short_address','string(//span[@class="listing-card-location"])',lambda x:[string.strip() for string in x])
        loader.add_value('city',self.get_city(response))
        loader.add_value('state',self.get_state(response))
        loader.add_value('zip',self.get_zip(response))
        loader.add_value('listed_by_company',self.get_listed_by_company(response))
        loader.add_value('listed_by_agent_name',self.get_listed_by_agent_name(response))
        loader.add_xpath('virtual_tour_url','//span[contains(text(),"3D Tour") or contains(text(),"Virtual Tour")]/ancestor::a/@href')
        #loader.add_value('city_id',response.meta['city_id'])
        yield loader.load_item()

    def get_total_pages(self,response:HtmlResponse) -> int :
        return max(
            [
                int(number) for number in  response.xpath('//li[@data-test="pagination-page-link"]/a/@href').re('page-(\d+)')
            ]
        )
    
    def get_city(self,response:HtmlResponse) -> str :
        return response.xpath('string(//span[@class="listing-card-location"])').get().strip().split(',')[0]
    
    def get_zip(self,response:HtmlResponse) -> str : 
        return response.xpath('string(//span[@class="listing-card-location"])').re('\d+')[0].strip()
    
    def get_listed_by_company(self,response:HtmlResponse) -> str :
        return response.xpath('string(//p[contains(text(),"Listed By")])').get().replace('Listed By','').split(',')[0].strip()
    
    def get_listed_by_agent_name(self,response:HtmlResponse) -> str : 
        return sub('\\d+-\d+-\d+|\(\d+\) \d+-\d+|\s\S+@[\s\S]+\.[\s\S]+','',response.xpath('string(//p[contains(text(),"Listed By")])').get().replace('Listed By','').split(',')[-1]).strip()
    
    def get_state(self,response:HtmlResponse) -> str :
        return self.states[
            response.url.split('/')[3].upper()
        ]
    
    def get_city_filter_name(self) -> str :
        return findall('/[a-z]{2}/([\s\S]+?)/',self.listing_url)[0].title()

if __name__ == '__main__' :
    listing_url = input('enter the listing url : ')
    process = CrawlerProcess(
        {
            #'HTTPCACHE_ENABLED' : True,
            'USER_AGENT':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'FEED_URI':'output.csv',
            'FEED_FORMAT':'csv',
        }
    )
    process.crawl(InfosSpider,listing_url)
    process.start()


