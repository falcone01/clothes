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
from urllib import quote,unquote
import json
from clothes.items import ClothesItem
from clothes.items import TagItem

tag_pattern_str =  ".*&tag=(.+?)&".decode("utf8")
tag_pattern = re.compile(tag_pattern_str,re.S)

class IChuanyiSpider(CrawlSpider):
	name = "ichuanyispider"
	allowed_domain = ["*.ichuangyi.com",'*.ichuangyi.cn']
	tag_list_url = "https://ichuanyi.com/pc.php?fromPageId=0&pageSize={0}&tag={1}&tagId=&method=suit.getListByTag&page={2}"
	initial_tags = ["民族风","逛街","约会","上学","出行","聚会","职场","高级灰","神秘黑","热情红","活力黄","青春绿","黑白灰","纯净白","水蓝色","浪漫紫","娇嫩粉","卡其色","显瘦","显高","肩宽","遮粗腿","大码","显白","遮肚腩","显脸小","平胸","遮大胸","遮PP","遮粗臂","学院","韩系","轻熟","欧美","日系","森系","休闲"]
	url_prefix = "https://image1.ichuanyi.cn/"
	detail_url  = "https://ichuanyi.com/m.php?method=suit.getInfo&needCommentCount=10&needCollectCount=10&viewUserId={0}&suitId={1}&isFromApp=1"
	
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
			for tag in self.initial_tags:
				tagItem = TagItem()
				tagItem['tag'] = tag
				tagItem['page'] = 0
				tagItem['page_size'] = 50
				tagItem['parsed'] = False
				self.tag_list.insert_one(dict(tagItem))
		else:
			logging.info("Already initialized")
	
	def start_requests(self):
		tag = self.tag_list.find_one({"$and":[{"parsed":False}]})
		if tag:
			#for tag in tags:
				#print tag['page_size']
				#print tag['tag']
			yield Request(self.tag_list_url.format(tag['page_size'],quote(tag['tag'].encode('utf-8')),tag['page']+1), callback = self.parse)
				#break
	
	def parse(self, response):
		logging.info("Start to parse %s"%(response.url))
		url = unquote(response.url)
		tagItem = None
		tagmatch = re.search(tag_pattern,url)
		if tagmatch:
			tag = tagmatch.group(1).strip()
			tagItem = self.tag_list.find_one({"tag":tag})
			self.tag_list.find_one_and_update({"tag":tag},{'$set':{'page':tagItem['page']+1}})
		#print url
		ret = None
		try:
			ret = json.loads(response.body)
		except Exception,e:
			ret = None
			logging.warning("Exception {0} in {1}, will mine next tag".format(e,response.url))
		
		if ret and ret['result'] == 0:
			suits = ret['data']['suits']
			if suits:
				for _,suit in suits.iteritems():
					user_id = suit['userId']
					suit_id = suit['suitId']
					image_site = suit['image']
					clothesItem = ClothesItem(user_id=user_id, suit_id=suit_id, search_tag = tagItem['tag'], image_urls=[self.url_prefix+image_site])
					#print self.detail_url.format(user_id,suit_id)
					yield Request(self.detail_url.format(user_id,suit_id), callback = self.parse_tags, meta={'item':clothesItem})
					#request.meta['item'] = clothesItem
					#yield request
					#break
				#print "crawl next page"
				url = self.tag_list_url.format(tagItem['page_size'],quote(tagItem['tag'].encode('utf-8')),tagItem['page']+2)
				yield Request( url, callback = self.parse)
			else:
				yield self.crawl_next(tagItem, True)
		else:
			yield self.crawl_next(tagItem, ret['result'] != 0)

	def crawl_next(self, tagItem, parsed = False):
		#print "crawl_next"
		if tagItem and parsed and not tagItem['parsed']:
				self.tag_list.find_one_and_update({"tag":tagItem['tag']},{'$set':{'parsed':True}})
		next_tag = self.tag_list.find_one({"$and":[{"parsed":False},{"page":0}]})
		if next_tag:
			logging.info("Find next un-crawled tag {0} start to crawl".format(next_tag['tag']))
			return Request(self.tag_list_url.format(next_tag['page_size'],quote(next_tag['tag'].encode('utf-8')),next_tag['page']+1), callback = self.parse)
	
	def parse_tags(self, response):
		item = response.meta['item']
		#print "in parse tag"
		ret = json.loads(response.body)
		#print ret.keys()
		#print ret['data'].keys()
		item['tags'] = []
		if 'tags' not in ret['data']:
			yield item
		else:
			tags = ret['data']['tags']		
			for _,tag in tags.iteritems():
				item['tags'].append(tag['name'])
			yield item
		
class IChuanyiTagSpider(CrawlSpider):
	name = "ichuanyitagspider"
	allowed_domain = ["*.ichuangyi.com",'*.ichuangyi.cn']
	detail_url  = "https://ichuanyi.com/m.php?method=suit.getInfo&needCommentCount=10&needCollectCount=10&viewUserId={0}&suitId={1}&isFromApp=1"
	
	def __init__(self, *a, **kw):
		super(IChuanyiSpider,self).__init__(*a,**kw)
		self.client = MongoClient()
		self.db = self.client.clothes
		self.clothes_list = self.db.clothes
	
	def start_requests(self):
		cloth = self.clothes_list.find_one({"tags":[]})
		if cloth:
			user_id = cloth['user_id']
			suit_id = cloth['suit_id']
			yield Request(self.detail_url.format(user_id,suit_id), callback = self.parse, meta = {'user_id':user_id,'suit_id':suit_id})
	
	def parse(self, response):
		user_id = response.meta['user_id']
		suit_id = response.meta['suit_id']
		tags = []
		ret = json.loads(response.body)
		if 'tags' not in ret['data']:
			logging.warning("No tags for suit {0}".format(suit_id))
		else:
			tags = ret['data']['tags']
			for _,tag in tags.iteritems():
				tags.append(tag['name'])
			self.clothes_list.find_one_and_update({"$and":[{"user_id":user_id},{"suit_id":suit_id}]},{"$set":{"tags":tags}})
			logging.info("Added tags for suit {0}".format(suit_id))
		cloth = self.clothes_list.find_one({"tags":[]})
		if cloth:
			user_id_next = cloth['user_id']
			suit_id_next = cloth['suit_id']
			yield Request(self.detail_url.format(user_id_next,suit_id_next), callback = self.parse, meta = {'user_id':user_id_next,'suit_id':suit_id_next})
	