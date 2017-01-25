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
    get_url_from_more_link,
    prepare_url
)

URL = 'http://cooperator.com/'
PUBLISHER_NAME = 'The Cooperator'
PUBLISHER_URL = 'cooperator.com'

def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

def get_tags(session, parser):
    tags = []
    post_tags_list = parser.find('span', class_="article__cats")
    if (post_tags_list):
        page_tags = post_tags_list.find_all('a')
        
        for tag in page_tags:
            (tag_object, result) = get_one_or_create(session, Tag, text=tag.string)
            tags.append(tag_object)
    return tags

def get_authors(session, parser):
    authors = []
    post_author = parser.find('div', class_="article__meta").find('span')
    
    if (post_author):
        author = post_author.get_text().replace('By', '')
        
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

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    session = get_session()

    (publication, publication_result) = get_one_or_create(
                session,
                Publication,
                create_method_kwargs=dict(
                    title=PUBLISHER_NAME,
                    url=PUBLISHER_URL
                ),
                url=PUBLISHER_URL
            )

    page = get_html(URL)
    parser = BeautifulSoup(page, "html.parser")
    articles_urls = parser.find_all('a', class_="article-small__link")
    
    urls = [
        url['href'] for url in articles_urls
    ]
    
    full_articles_urls = []
    for url in urls:
        page = get_html("".join([URL, url]))

        full_article_url = BeautifulSoup(page, "html.parser").find('a', class_="article__more")

        if (full_article_url is not None):
            full_articles_urls.append(full_article_url['href'] )
    
    for article_url in full_articles_urls:

        full_article_url = "".join([URL, article_url])

        page = get_html(full_article_url)
        parser = BeautifulSoup(page, "html.parser")

        body = " ".join(
            [p.get_text() 
                for p in parser.find('div', class_="article__content").find_all('p')
            ]
        )

        (article, article_result) = get_one_or_create(
            session,
            Article,
            create_method_kwargs=dict(
                guid=full_article_url,
                title=parser.find('h1', class_="article__title").get_text(),
                body=body,
                url=full_article_url,
                # posted=datetime(*entry.published_parsed[:6]),
                publication=publication
            ),
            guid=full_article_url
        )
        session.commit()

        article.authors = get_authors(session, parser)
        article.tags = get_tags(session, parser)


        image = parser.find('article', class_="article").find('img')['src']
        image_url = list(urllib.parse.urlsplit("".join([URL, image])))
        image_url[3] = ''
        image_url = urllib.parse.urlunsplit(image_url)

        try:
            article.photo1_url = image_url
            article.photo1_filename = save_image(image_url)
        except IndexError:
            #just skip 
            pass

        session.commit()

    session.close()

    print("\nJob is done")

if __name__ == '__main__':
    main()