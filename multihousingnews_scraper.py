#!/usr/bin/env python3

import os
import sys
import re

import urllib.request
import feedparser

from datetime import datetime

from urllib.request import urlretrieve
from bs4 import BeautifulSoup

from models import Article, Tag, Author, Publication
from utils import OUTPUT_DIR, get_one_or_create, get_session, save_image

URL ='https://www.multihousingnews.com/feed/'
PUBLISHER_NAME = 'MNH (Mutli-housing news)'
PUBLISHER_URL = 'www.multihousingnews.com'
PUBLISHER_RSS_URL = URL


def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

def get_tags(session, tags):
    result = []
    for tag in tags:
        (tag_object, is_added) = get_one_or_create(session, Tag, text=tag['term'])
        result.append(tag_object)
    return result

def get_authors(session, parser):
    authors = []
    post_author = parser.find('li', class_="post-author")
    if (post_author):
        author = post_author.get_text().replace('by ', '')
        fullname = author.split()
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

        body = " ".join(
            [p.get_text() 
                for p in parser.find('div', class_="content").find_all('p')
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
        article.tags = get_tags(session, entry.tags)
        
        article.authors = get_authors(session, parser)
        image_url = parser.find('div', class_="content").find('img')['src']
        try:
            article.photo1_url = image_url
            image_url = url = re.sub('\?.*$', '', image_url)
            article.photo1_filename = save_image(image_url)
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