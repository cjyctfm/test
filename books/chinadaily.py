#!/usr/bin/env python
# -*- coding:utf-8 -*-

from datetime import datetime # 导入时间处理模块datetime
from base import BaseFeedBook # 继承基类BaseFeedBook
from lib.urlopener import URLOpener # 导入请求URL获取页面内容的模块
from bs4 import BeautifulSoup # 导入BeautifulSoup处理模块

# 返回此脚本定义的类名
def getBook():
    return ChinaDaily

# 继承基类BaseFeedBook
class ChinaDaily(BaseFeedBook):
    # 设定生成电子书的元数据
    title = u'China Daily' # 设定标题
    __author__ = u'China Daily' # 设定作者
    description = u'Chinadaily.com.cn is the largest English portal in China. ' # 设定简介
    language = 'en' # 设定语言

    coverfile = 'cv_chinadaily.jpg' # 设定封面图片
    mastheadfile = 'mh_chinadaily.gif' # 设定标头图片

    # 指定要提取的包含文章列表的主题页面链接
    # 每个主题是包含主题名和主题页面链接的元组
    feeds = [
        (u'National affairs', 'http://www.chinadaily.com.cn/china/governmentandpolicy'),
        (u'Society', 'http://www.chinadaily.com.cn/china/society'),
    ]

    page_encoding = 'utf-8' # 设定待抓取页面的页面编码
    fulltext_by_readability = False # 设定手动解析网页

    # 设定内容页需要保留的标签
    keep_only_tags = [
        dict(name='span', class_='info_l'),
        dict(name='div', id='Content'),
    ]

    max_articles_per_feed = 40 # 设定每个主题下要最多可抓取的文章数量
    oldest_article = 1 # 设定文章的时间范围。小于等于365则单位为天，否则单位为秒，0为不限制。

    # 提取每个主题页面下所有文章URL
    def ParseFeedUrls(self):
        urls = [] # 定义一个空的列表用来存放文章元组
        # 循环处理fees中两个主题页面
        for feed in self.feeds:
            # 分别获取元组中主题的名称和链接
            topic, url = feed[0], feed[1]
            # 把抽取每个主题页面文章链接的任务交给自定义函数ParsePageContent()
            self.ParsePageContent(topic, url, urls, count=0)
        # print urls
        # exit(0)
        # 返回提取到的所有文章列表
        return urls

    # 该自定义函数负责单个主题下所有文章链接的抽取，如有翻页则继续处理下一页
    def ParsePageContent(self, topic, url, urls, count):
        # 请求主题页面链接并获取其内容
        result = self.GetResponseContent(url)
        # 如果请求成功，并且页面内容不为空
        if result.status_code == 200 and result.content:
            # 将页面内容转换成BeatifulSoup对象
            soup = BeautifulSoup(result.content, 'lxml')
            # 找出当前页面文章列表中所有文章条目
            items = soup.find_all(name='span', class_='tw3_01_2_t')

            # 循环处理每个文章条目
            for item in items:
                title = item.a.string # 获取文章标题
                link = item.a.get('href') # 获取文章链接
                link = BaseFeedBook.urljoin(url, link) # 合成文章链接
                count += 1 # 统计当前已处理的文章条目
                # 如果处理的文章条目超过了设定数量则中止抽取
                if count > self.max_articles_per_feed:
                    break
                # 如果文章发布日期超出了设定范围则忽略不处理
                if self.OutTimeRange(item):
                    continue
                # 将符合设定文章数量和时间范围的文章信息作为元组加入列表
                urls.append((topic, title, link, None))

            # 如果主题页面有下一页，且已处理的文章条目未超过设定数量，则继续抓取下一页
            next = soup.find(name='a', string='Next')
            if next and count < self.max_articles_per_feed:
                url = BaseFeedBook.urljoin(url, next.get('href'))
                self.ParsePageContent(topic, url, urls, count)
        # 如果请求失败则打印在日志输出中
        else:
            self.log.warn('Fetch article failed(%s):%s' % \
                (URLOpener.CodeMap(result.status_code), url))

    # 此函数负责判断文章是否超出指定时间范围，是返回 True，否则返回False
    def OutTimeRange(self, item):
        current = datetime.utcnow() # 获取当前时间
        updated = item.find(name='b').string # 获取文章的发布时间
        # 如果设定了时间范围，并且获取到了文章发布时间
        if self.oldest_article > 0 and updated:
            # 将文章发布时间字符串转换成日期对象
            updated = datetime.strptime(updated, '%Y-%m-%d %H:%M')
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

    # 清理文章URL附带字符
    def processtitle(self, title):
        return title.replace(u' - Chinadaily.com.cn', '')

    # 在文章内容被正式处理前做一些预处理
    def preprocess(self, content):
        # 将页面内容转换成BeatifulSoup对象
        soup = BeautifulSoup(content, 'lxml')
        # 调用处理内容分页的自定义函数SplitJointPagination()
        content = self.SplitJointPagination(soup)
        # 返回预处理完成的内容
        return unicode(content)

    # 此函数负责处理文章内容页面的翻页
    def SplitJointPagination(self, soup):
        # 如果文章内容有下一页则继续抓取下一页
        next = soup.find(name='a', string='Next')
        if next:
            # 含文章正文的标签
            tag = dict(name='div', id='Content')
            # 获取下一页的内容
            result = self.GetResponseContent(next.get('href'))
            post = BeautifulSoup(result.content, 'lxml')
            # 将之前的内容合并到当前页面
            soup = BeautifulSoup(unicode(soup.find(**tag)), 'html.parser')
            soup.contents[0].unwrap()
            post.find(**tag).append(soup)
            # 继续处理下一页
            return self.SplitJointPagination(post)
        # 如果有翻页，返回拼接的内容，否则直接返回传入的​内容
        return soup

    # 此自定义函数负责请求传给它的链接并返回响应内容
    def GetResponseContent(self, url):
        opener = URLOpener(self.host, timeout=self.timeout, headers=self.extra_header)
        return opener.open(url)
