# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ClothesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
	user_id = scrapy.Field()
	suit_id = scrapy.Field()
	image_urls  = scrapy.Field()
	images = scrapy.Field()
	tags = scrapy.Field()
	search_tag = scrapy.Field()
	
class TagItem(scrapy.Item):
	tag = scrapy.Field()
	parsed = scrapy.Field()
	page = scrapy.Field()
	page_size = scrapy.Field()
