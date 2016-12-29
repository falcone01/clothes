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
from clothes.items import TagItem

class IChuanyiSpider(CrawlSpider):
	name = "ichuanyispider"
	allowed_domain = ["ichuangyi.com"]
	tag_list_url = "http://ichuanyi.com/pc.php?fromPageId=0&pageSize={0}&tag={1}&tagId=&method=suit.getListByTag&page={2}"
	initial_tags = ["逛街","约会","上学","出行","聚会","职场","高级灰","神秘黑","热情红","活力黄","青春绿","黑白灰","纯净白","水蓝色","浪漫紫","娇嫩粉","卡其色","显瘦","显高","肩宽","遮粗腿","大码","显白","遮肚腩","显脸小","平胸","遮大胸","遮PP","遮粗臂","学院","韩系","轻熟","欧美","日系","森系","休闲","民族风"]
	url_prefix = "https://image1.ichuanyi.cn/"
	#start_urls = [tag_list_url.format(quote('民族风'))]
	
	def __init__(self, *a, **kw):
		super(IChuanyiSpider,self).__init__(*a,**kw)
		self.client = MongoClient()
		self.db = self.client.clothes
		self.tag_list = self.db.tags
		self.clothes_list = self.db.clothes
		self.init_tags()
	
	def init_tags(self):
		ret = self.tag_list.find_one()
		if not ret:
			for tag in self.init_tags:
				tagItem = TagItem()
				tagItem['tag'] = tag
				tagItem['page'] = 1
				tagItem['page_size'] = 1000
				tagItem['parsed'] = false
				self.tag_list.insert_one(dict(tagItem))
		else:
			logging.info("Already initialized")
	
	def start_requests(self):
		tags = self.tag_list.find({"parsed":false})
		if tags:
			for tag in tags:
				yield Request(tag_list_url.format(tag['page_size'],quote(tag['tag']),tag['page']), callback = self.parse)
	
	def parse(self, response):
		logging.info("Start to parse %s"%(response.url))
		ret = json.loads(response.body)
		suits = ret['data']['suits']
		if suits:
			for _,suit in suits.iteritems():
				user_id = suit['userId']
				suit_id = suit['suitId']
				image_site = suit['image']
				clothesItem = ClothesItem(user_id=user_id, suit_id=suit_id,image_urls=[self.url_prefix+image_site])
				yield clothesItem