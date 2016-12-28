# -*- coding: utf-8 -*-
import sys
reload(sys)

sys.setdefaultencoding("utf-8")

from scrapy.spiders import CrawlSpider,Rule
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.linkextractors import LinkExtractor
import re
import logging
from pymongo import MongoClient
from urllib import quote
import json
from clothes.items import ClothesItem

class IChuanyiSpider(CrawlSpider):
	name = "ichuanyispider"
	allowed_domain = ["ichuangyi.com"]
	tag_list_url = "http://ichuanyi.com/pc.php?fromPageId=0&pageSize=1000&page=1&tag={0}&tagId=&method=suit.getListByTag&page=1"
	tags = ["民族风"]
	url_prefix = "https://image1.ichuanyi.cn/"
	start_urls = [tag_list_url.format(quote('民族风'))]
	
	def parse(self, response):
		ret = json.loads(response.body)
		#print(len(x['data']['suits']))
		first = ret['data']['suits']['0']
		image_site  = first['image']
		user_id = first["userId"]
		suit_id = first['suitId']
		print(self.url_prefix+image_site)
		yield ClothesItem(user_id=user_id, suit_id=suit_id,image_urls=[self.url_prefix+image_site])