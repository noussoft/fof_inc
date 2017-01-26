#!/usr/bin/env python3

import os
import sys

import urllib.request
import feedparser

from datetime import datetime

from bs4 import BeautifulSoup

from models import Article, Tag, Author, Publication
from utils import (
    OUTPUT_DIR,
    get_one_or_create,
    get_session,
    save_image,
    get_url_from_more_link
)

URL = 'http://feeds.feedburner.com/trdnews?format=xml'
PUBLISHER_NAME = 'The Real Deal'
PUBLISHER_URL = 'therealdeal.com'
PUBLISHER_RSS_URL = URL

def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

def get_tags(session, parser):
    tags = []
    post_tags_list = parser.find('div', class_="post-tags-list")
    if (post_tags_list):
        page_tags = post_tags_list.find_all('a')
        
        for tag in page_tags:
            (tag_object, result) = get_one_or_create(session, Tag, text=tag.string)
            tags.append(tag_object)
    return tags

def get_authors(session, parser):
    authors = []
    post_authors_list = parser.find('em', class_="author vcard")
    if (post_authors_list):
        page_authors = post_authors_list.find_all('a')
        
        for author in page_authors:
            if (author.string is not None):
                fullname = author.string.split()
                first = fullname[0]
                if len(fullname) >=2:
                    last = fullname[1]
                else:
                    last = ''
                (author_object, result) = get_one_or_create(
                                            session, Author, first=first, last=last)
                authors.append(author_object)
    return authors

def get_images(parser):
    images = []
    post_image_list = parser.find('div', class_="post-content-box")
    if (post_image_list):
        page_images = post_image_list.find_all('img')
        
        images = [image['src'] for image in page_images]
    return images

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    session = get_session()

    (publication, publication_result) = get_one_or_create(
                session,
                Publication,
                create_method_kwargs=dict(
                    title=PUBLISHER_NAME,
                    url=PUBLISHER_URL,
                    rss_url=PUBLISHER_RSS_URL
                ),
                url=PUBLISHER_URL
            )

    data = feedparser.parse(URL)
    
    for entry in data.entries:

        article_url = get_url_from_more_link(entry.content[0]['value'])
        if (article_url is not None):
            
            if (urllib.parse.urlsplit(article_url)[1] == PUBLISHER_URL):

                page = get_html(article_url)
                parser = BeautifulSoup(page, "html.parser")
                content = parser.find('div', class_="post-content-box")
                if (content is not None):
                    body = " ".join(
                        [p.get_text() 
                            for p in content.find_all('p')
                        ]
                    )
                else:
                    body=BeautifulSoup(entry.content[0]['value'], "html.parser").get_text()
            else:
                body=BeautifulSoup(entry.content[0]['value'], "html.parser").get_text()

            (article, article_result) = get_one_or_create(
                session,
                Article,
                create_method_kwargs=dict(
                    guid=entry.guid,
                    title=entry.title,
                    body=body,
                    url=article_url,
                    posted=datetime(*entry.published_parsed[:6]),
                    publication=publication
                ),
                guid=entry.guid
            )
            session.commit()
            
            parser = BeautifulSoup(page, "html.parser")
            article.tags = get_tags(session, parser)
            article.authors = get_authors(session, parser)
            images = get_images(parser)
            try:
                article.photo1_url = images[0]
                article.photo1_filename = save_image(images[0])
            except IndexError:
                #just skip 
                pass
            try:
                article.photo2_url = images[1]
                article.photo2_filename = save_image(images[1])
            except IndexError:
                #just skip 
                pass

            session.commit()

    publication.last_run = datetime.now()
    session.commit()
    session.close()

    print("\nJob is done")

if __name__ == '__main__':
    main()