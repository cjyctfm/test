#!/usr/bin/env python
# -*- coding:utf-8 -*-

from base import BaseFeedBook # 继承基类BaseFeedBook
from lib.urlopener import URLOpener # 导入请求URL获取页面内容的模块
from bs4 import BeautifulSoup # 导入BeautifulSoup处理模块
from datetime import datetime # 导入时间处理模块datetime
# 返回此脚本定义的类名
def getBook():
    return ZaoBao

# 继承基类BaseFeedBook
class ZaoBao(BaseFeedBook):
    # 设定生成电子书的元数据
    title = u'ZaoBao' # 设定标题
    __author__ = u'ZaoBao' # 设定作者
    description = u'新加坡、中国、亚洲和国际的即时、评论、商业、体育、生活、科技与多媒体新闻,尽在联合早报。 ' # 设定简介
    language = 'en' # 设定语言

    coverfile = 'cv_chinadaily.jpg' # 设定封面图片
    mastheadfile = 'mh_chinadaily.gif' # 设定标头图片

    # 指定要提取的包含文章列表的主题页面链接
    # 每个主题是包含主题名和主题页面链接的元组
    feeds = [
        (u'中国', 'https://www.zaobao.com/news/china'),
        (u'国际', 'https://www.zaobao.com/news/world'),
        (u'东南亚', 'https://www.zaobao.com/news/sea')
        
     ]

    page_encoding = 'utf-8' # 设定待抓取页面的页面编码
    fulltext_by_readability = False # 设定手动解析网页

    # 设定内容页需要保留的标签
    keep_only_tags = [
        dict(name='span', class_='datestamp date-published meta-date-published'),
        dict(name='div', id='FineDining'),
    ]

    # 提取每个主题页面下所有文章URL
    def ParseFeedUrls(self):
        urls = [] # 定义一个空的列表用来存放文章元组
        # 循环处理fees中两个主题页面
        for feed in self.feeds:
            # 分别获取元组中主题的名称和链接
            topic, url = feed[0], feed[1]
            # 请求主题链接并获取相应内容
            opener = URLOpener(self.host, timeout=self.timeout)
            result = opener.open(url)
            # 如果请求成功，并且页面内容不为空
            if result.status_code == 200 and result.content:
                # 将页面内容转换成BeatifulSoup对象
                soup = BeautifulSoup(result.content, 'lxml')
                # 找出当前页面文章列表中所有文章条目
                items=soup.find('div',class_='grid').find_all(name='div', class_='content')
                # 循环处理每个文章条目
                for item in items:
                    title = item.span.string # 获取文章标题
                    link = item.a.get('href') # 获取文章链接
                    link = BaseFeedBook.urljoin(url, link) # 合成文章链接
                    if self.OutTimeRange(item):
                        continue
                    urls.append((topic, title, link, None)) # 把文章元组加入列表
            # 如果请求失败通知到日志输出中
            else:
                self.log.warn('Fetch article failed(%s):%s' % \
                    (URLOpener.CodeMap(result.status_code), url))
        # 返回提取到的所有文章列表
        return urls
    oldest_article = 1 # 设定文章的时间范围。小于等于365则单位为天，否则单位为秒，0为不限制。
    def OutTimeRange(self, item):
        current = datetime.utcnow() # 获取当前时间
        updated = item.next_sibling.string # 获取文章的发布时间
        # 如果设定了时间范围，并且获取到了文章发布时间
        if self.oldest_article > 0 and updated:
            # 将文章发布时间字符串转换成日期对象
            updated = datetime.strptime(updated, '%d/%m/%Y')
            delta = current - updated # 当前时间减去文章发布时间
            # 将设定的时间范围转换成秒，小于等于365则单位为天，否则则单位为秒
            if self.oldest_article > 365:
                threshold = self.oldest_article # 以秒为单位的直接使用秒
            else:
                threshold = 86400 * self.oldest_article # 以天为单位的转换为秒
            # 如果文章发布时间超出设定时间范围返回True
            if (threshold < delta.days * 86400 + delta.seconds):
                return True
        # 如果设定时间范围为0，文章没超出设定时间范围（或没有发布时间），则返回False
        return False
