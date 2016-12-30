# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
import json
import logging
from pymongo import MongoClient
from clothes.items import TagItem

client = MongoClient()
db = client.clothes
clothes_list = db.clothes
tag_list = db.tags

def find_exist(user_id, suit_id):
	global clothes_list
	ret = clothes_list.find_one({"$and":[{"user_id":user_id},{"suit_id":suit_id}]})
	if ret:
		return True
	else:
		return False

		
def add_tag(tags):
	for tag in tags:
		ret = tag_list.find_one({"tag":tag})
		if not ret:
			tagItem = TagItem()
			tagItem['tag'] = tag
			tagItem['page'] = 0
			tagItem['page_size'] = 50
			tagItem['parsed'] = False
			tag_list.insert_one(dict(tagItem))
			logging.info("add new tag {0}".format(tag))

class ClothesPipeline(object):
	global clothes_list
	count = 0
	def process_item(self, item, spider):
	#	logging.info("store item {0}".format(item['suit_id']))
	#print item
		ret = find_exist(item['user_id'],item['suit_id'])
		if ret:
			logging.info("Already have such clothes with user id {0} and suit id {1}".format(item['user_id'],item['suit_id']))
		else:
			add_tag(item['tags'])
			clothes_list.insert_one(dict(item))
			self.count += 1
			logging.info("Add new item with suit id {0}".format(item['suit_id']))
			if self.count % 50 == 0:
				logging.info("Added {0} clothes".format(self.count))
		#return item