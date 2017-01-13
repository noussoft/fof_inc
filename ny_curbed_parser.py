#!/usr/bin/env python3

import os
import sys

import urllib.request
import feedparser

from datetime import datetime

from urllib.request import urlretrieve
from bs4 import BeautifulSoup

from models import Article, Tag, Author
from utils import OUTPUT_DIR, get_one_or_create, get_session, save_image

URL ='http://ny.curbed.com/rss/smartnews.xml'


def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

def get_tags(session, tags):
    result = []
    for tag in tags:
        (tag_object, is_added) = get_one_or_create(session, Tag, text=tag['term'])
        result.append(tag_object)
    return result

def get_authors(session, authors):
    result = []
        
    for author in authors:
        fullname = author['name'].split()
        first = fullname[0]
        if len(fullname) >=2:
            last = fullname[1]
        else:
            last = ''
        (author_object, is_added) = get_one_or_create(
                                    session, Author, first=first, last=last)
        result.append(author_object)
    return result

def get_images(parser):
    images = [image['src'] for image in parser.find_all('img')]
    if len(images) > 2:
        return images[0:2]
    return images

def main():

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    session = get_session()
    data = feedparser.parse(URL)

    for entry in data.entries:

        (article, article_result) = get_one_or_create(
            session,
            Article,
            create_method_kwargs=dict(
                guid=entry.guid,
                title=entry.title,
                body=BeautifulSoup(entry.content[0]['value'], "html.parser").get_text(),
                url=entry.link,
                posted=datetime(*entry.published_parsed[:6])
            ),
            guid=entry.guid
        )
        session.commit()
        
        # article.tags = get_tags(session, entry.tags)
        article.authors = get_authors(session, entry.authors)

        parser = BeautifulSoup(entry.content[0]['value'], "html.parser")
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

    session.close()

    print("\nJob is done")

if __name__ == '__main__':
    main()