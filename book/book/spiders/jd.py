# -*- coding: utf-8 -*-
import scrapy
import urllib
import json
from copy import deepcopy

class JdSpider(scrapy.Spider):
    name = 'jd'
    allowed_domains = ['jd.com','p.3.cn']
    start_urls = ['https://book.jd.com/booksort.html']

    def parse(self, response):
        dt_list = response.xpath("//div[@class='mc']/dl/dt")
        for dt in dt_list:
            item = {}
            item["big_cate"] = dt.xpath("./a/text()").extract_first()
            em_list = dt.xpath("./following-sibling::dd[1]/em")  # 小分类列表
            for em in em_list:
                item["s_cate"] = em.xpath("./a/text()").extract_first()
                item["s_href"] = em.xpath("./a/@href").extract_first()
                item["s_href"] = urllib.parse.urljoin(response.url,item["s_href"])
                if item["s_href"] is not None:
                    yield scrapy.Request(
                        item["s_href"],
                        callback=self.parse_detail,
                        meta={"item":deepcopy(item)}
                  )

    def parse_detail(self, response):
        item = response.meta["item"]

        li_list = response.xpath("//div[@id='plist']/ul/li")
        for li in li_list:
            item["book_name"] = li.xpath(".//div[@class='p-name']/a/em/text()").extract_first().strip()
            item["book_img"] = urllib.parse.urljoin(response.url,li.xpath(".//div[@class='p-img']//img/@src").extract_first())
            item["author"] = li.xpath(".//span[@class='author_type_1']/a/@title").extract()
            item["publish_by"] = li.xpath(".//span[@class='p-bi-store']/a/@title").extract_first()
            item["ems"] = li.xpath(".//div[@class='p-service']/text()").extract_first().strip()
            item["sku_id"] = li.xpath("./div/@data-sku").extract_first()

            # yield item
            yield scrapy.Request(
                "https://p.3.cn/prices/mgets?skuIds=J_{}".format(item["sku_id"]),
                callback=self.parse_price,
                meta={"item":deepcopy(item)}
            )


        next_url = urllib.parse.urljoin(response.url,response.xpath(".//a[@class='pn-next']/@href").extract_first())
        if next_url is not None:
            yield scrapy.Request(
                next_url,
                callback=self.parse_detail,
                meta={"item":item}
            )


    def parse_price(self, response):
        item = response.meta["item"]
        item["price"] = json.loads(response.body.decode())[0]["op"]
        yield item
