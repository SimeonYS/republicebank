import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import RrepublicebankItem
from itemloaders.processors import TakeFirst
import requests
import json
from scrapy import Selector
pattern = r'(\xa0)?'

url = "https://republicebank.com/wp-admin/admin-ajax.php"

payload = "action=vamtam-load-more&query%5Bposts_per_page%5D=6&query%5Bpost_type%5D=post&query%5Bpaged%5D={}&other_vars%5Bimage%5D=true&other_vars%5Bshow_content%5D=true&other_vars%5Bwidth%5D=one_half&other_vars%5Bnews%5D=true&other_vars%5Bcolumn%5D=2&other_vars%5Blayout%5D=masonry"
headers = {
  'authority': 'republicebank.com',
  'pragma': 'no-cache',
  'cache-control': 'no-cache',
  'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
  'accept': '*/*',
  'x-requested-with': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
  'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'origin': 'https://republicebank.com',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://republicebank.com/news/page/2/',
  'accept-language': 'en-US,en;q=0.9',
  'cookie': '_ga=GA1.2.587490268.1617279874; _gid=GA1.2.1111689737.1617279874; psCurrentState=Ready; __zlcmid=13OjvJL0WRFZaaw; _gat_gtag_UA_28556307_1=1; vngage.id=5fcb224f-b6e2-4cf2-ab83-43abf9ea4dc8+k4ZO4UI7IPNw2t9jFF1K2G6vzAiOtFnf3TfvluW5QA=; vngage.vid=431A9BF2-0A68-4E50-A36F-E7104F0FBADD; vngage.lkvt=595A8E9E-3CD6-42FD-B74E-CA650F74A92E'
}

class RrepublicebankSpider(scrapy.Spider):
	name = 'republicebank'
	page = 2
	start_urls = ['https://republicebank.com/news/']

	def parse(self, response):
		data = requests.request("POST", url, headers=headers, data=payload.format(self.page))
		data = json.loads(data.text)

		posts = Selector(text=data['content']).xpath('//div[@class="standard-post-format clearfix as-image "]')
		for post in posts:
			date = post.xpath('.//div[@class="post-date"]/text()').get().strip()
			link = post.xpath('.//h3/a/@href').get()
			yield response.follow(link, self.parse_post, cb_kwargs=dict(date=date))

		if data['content']:
			self.page += 1
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response, date):
		title = response.xpath('//span[@class="entry-title"]/text()').get()
		content = response.xpath('//div[@class="wpv-grid grid-1-1  first unextended"]//text()[not (ancestor::style)] | //div[@class="post-content the-content"]//text()[not (ancestor::style)]').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=RrepublicebankItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
