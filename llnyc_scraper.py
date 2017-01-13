#!/usr/bin/env python3

import os
import sys

import urllib.request
import feedparser

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils.functions import database_exists, create_database

from urllib.request import urlretrieve
from bs4 import BeautifulSoup

from settings import DB_USER, DB_PASSWORD, DB_NAME
from models import Base, Article, Tag, Author
from utils import OUTPUT_DIR, get_one_or_create, save_image

URL ='http://www.llnyc.com/feed'

def get_session():
    engine = create_engine(
        'mysql://{}:{}@localhost/{}?charset=utf8'.format(DB_USER, DB_PASSWORD, DB_NAME),
        poolclass=NullPool)
    Session = sessionmaker(bind=engine)
    session = Session()

    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.create_all(engine)

    return session

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
    return [image['src'] for image in parser.find_all('img')]

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
        
        article.tags = get_tags(session, entry.tags)
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