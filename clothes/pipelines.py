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

client = MongoClient()
db = client.clothes
clothes_list = db.clothes

class ClothesPipeline(object):
	global clothes_list
    def process_item(self, item, spider):
        ret = clothes_list.find_one({"$and":[{"user_id":item['user_id']},{"suit_id":item['suit_id']}]})
		if ret:
			logging.info("Already have such clothes with user id {0} and suit id {1}".format(item['user_id'],item['suit_id']))
		else:
			clothes_list.insert_one(dict(item))
		return item

		
class ClothesImagePipeline(ImagesPipeline):
	def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url)

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        item['image_paths'] = image_paths
        return item