# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import datetime
import re

import scrapy

# 时间转换
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join

# 字符串转换时间方法
from ArticleSpider.settings import SQL_DATETIME_FORMAT


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


# 获取字符串内数字方法
def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums


# 去除标签中提取的评论方法
def remove_comment_tags(value):
    if "评论" in value:
        return ""
    else:
        return value


def exclude_none(value):
    if value:
        return value
    else:
        value = "无"
        return value


# 直接获取值方法
def return_value(value):
    return value


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader实现默认提取第一个
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(
        # input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        # 使用自定义的outprocessor覆盖原始的take first 使得image_url是一个列表。
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        # input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    # 因为tag本身是list，所以要重写
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field()
    crawl_time = scrapy.Field()

    def make_data_clean(self):
        front_image_url = ""
        # content = remove_tags(self["content"])
        self["crawl_time"] = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)
        if self["front_image_url"]:
            self["front_image_url"] = self["front_image_url"][0]
        str = self["create_date"].strip().replace("·", "").strip()
        self["create_date"] = datetime.datetime.strptime(str, "%Y/%m/%d").date()
        nums = 0
        value = self["praise_nums"]
        match_re = re.match(".*?(\d+).*", value)
        if match_re:
            nums = int(match_re.group(1))
        else:
            nums = 0
        self["praise_nums"] = nums

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO jobbole_article(title, url, url_object_id,create_date, fav_nums, front_image_url, front_image_path,praise_nums, comment_nums, tags, content,crawl_time)
            VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s,%s) ON DUPLICATE KEY UPDATE fav_nums=VALUES(fav_nums),praise_nums=VALUES(praise_nums),comment_nums=VALUES(comment_nums),crawl_time=VALUES(crawl_time)
        """
        self.make_data_clean()
        params = (
            self["title"],
            self["url"],
            self["url_object_id"],
            self["create_date"],
            self["fav_nums"],
            self["front_image_url"],
            self["front_image_path"],
            self["praise_nums"],
            self["comment_nums"],
            self["tags"],
            self["content"],
            self["crawl_time"]
        )
        return insert_sql, params
