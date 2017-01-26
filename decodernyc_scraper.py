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

URL = 'http://www.decodernyc.com/feed/'
PUBLISHER_NAME = 'Decoder (NYC)'
PUBLISHER_URL = 'www.decodernyc.com'
PUBLISHER_RSS_URL = URL

def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

def get_tags(session, parser):
    tags = []
    post_tags_list = parser.find('span', class_="thecategories")
    if (post_tags_list):
        page_tags = post_tags_list.find_all('a')
        
        for tag in page_tags:
            (tag_object, result) = get_one_or_create(session, Tag, text=tag.string)
            tags.append(tag_object)
    return tags

def get_authors(session, parser):
    result = []
      
    post_authors_list = parser.find('span', class_="theauthor")
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
                (author_object, is_added) = get_one_or_create(
                                            session, Author, first=first, last=last)
                result.append(author_object)
    return result

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
        article_url = get_url_from_more_link(entry.description, link_text="(more...)")

        page = get_html(article_url)
        parser = BeautifulSoup(page, "html.parser")

        body = " ".join(
            [p.get_text() 
                for p in parser.find('div', class_="entry-content").find_all('p')
            ]
        )

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
        article.authors = get_authors(session, parser)
        article.tags = get_tags(session, parser)
        
        session.commit()

    publication.last_run = datetime.now()
    session.commit()
    session.close()

    print("\nJob is done")

if __name__ == '__main__':
    main()