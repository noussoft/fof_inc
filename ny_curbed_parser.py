#!/usr/bin/env python3

import os
import sys

import urllib.request
import feedparser

from datetime import datetime

from urllib.request import urlretrieve
from bs4 import BeautifulSoup

from models import Article, Tag, Author, Publication
from utils import OUTPUT_DIR, get_one_or_create, get_session, save_image

URL ='http://ny.curbed.com/rss/smartnews.xml'
PUBLISHER_NAME = 'Curbed (New York)'
PUBLISHER_URL = 'ny.curbed.com'
PUBLISHER_RSS_URL = URL


def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

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

        page = get_html(entry.link)
        parser = BeautifulSoup(page, "html.parser")
        content = parser.find('div', class_="c-entry-content")
        body=''
        if (content is not None):
            body = " ".join(
                [p.get_text() 
                    for p in content.find_all('p')
                ]
            )

        (article, article_result) = get_one_or_create(
            session,
            Article,
            create_method_kwargs=dict(
                guid=entry.guid,
                title=entry.title,
                body=body,
                url=entry.link,
                posted=datetime(*entry.published_parsed[:6]),
                publication=publication
            ),
            guid=entry.guid
        )
        session.commit()
        
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

    publication.last_run = datetime.now()
    session.commit()
    session.close()

    print("\nJob is done")

if __name__ == '__main__':
    main()