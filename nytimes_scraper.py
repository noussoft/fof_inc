#!/usr/bin/env python3

import os
import sys

import iso8601

import urllib.request
import feedparser

from datetime import datetime

from bs4 import BeautifulSoup

from http.cookiejar import CookieJar

from models import Article, Tag, Author, Publication
from utils import (
    OUTPUT_DIR,
    get_one_or_create,
    get_session,
    save_image,
    get_url_from_more_link
)

URL = 'https://www.rsssearchhub.com/feed/e1682c8e8e4b5b0846493351d287e7cf/nyt-commercial-real-estate'
PUBLISHER_NAME = 'Commercial Real Estate (NYT)'
PUBLISHER_URL = 'www.nytimes.com'
PUBLISHER_RSS_URL = URL

def get_feed(url):
    response = urllib.request.urlopen(url)
    return response.read()

def get_html(url):
    request = urllib.request.Request(
        url,
        None,
        {
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686; G518Rco3Yp0uLV40Lcc9hAzC1BOROTJADjicLjOmlr4=) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'
        }
    )
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    response = opener.open(request)
    raw_response = response.read().decode()
    response.close()
    return raw_response

def get_images(parser):
    images = []
    image_list = parser.find_all('img', class_="media-viewer-candidate")
    if (image_list):
        
        images = [image['src'] for image in image_list]
    return images

def get_authors(session, parser):
    result = []
      
    post_author = parser.find('span', class_="byline-author")
    if (post_author):
        author = post_author['data-byline-name']
        if (author is not None):
            fullname = author.split()
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

    page = get_feed(URL)
    parser = BeautifulSoup(page, "html.parser")

    articles_urls = [article.find('a')['href'] for article in parser.find_all('article')[1:]]
    
    for article_url in articles_urls:

        article_page = get_html(article_url)
        article_parser = BeautifulSoup(article_page, "html.parser")
    
        body = " ".join(
            [p.get_text() 
                for p in article_parser.find('div', class_="story-body").find_all('p')
            ]
        )

        (article, article_result) = get_one_or_create(
            session,
            Article,
            create_method_kwargs=dict(
                guid=article_url,
                title=article_parser.find('h1', class_="headline").get_text(),
                body=body,
                url=article_url,
                posted=iso8601.parse_date(article_parser.find('time', class_="dateline")['content']),
                publication=publication
            ),
            guid=article_url
        )
        session.commit()

        article.authors = get_authors(session, article_parser)
        images = get_images(article_parser)
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