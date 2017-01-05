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

from settings import DB_USER, DB_PASSWORD, DB_NAME, URL
from models import Base, Article, Tag

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

def main():

    session = get_session();
    data = feedparser.parse(URL)
    
    articles = []
    for entry in data.entries:

        page = get_html(entry.comments)
        soup = BeautifulSoup(page, "html.parser")
        page_article = soup.find('div', class_="entry-post")
        
        tags = []
        post_tags_list = soup.find('div', class_="post-tags-list")
        if (post_tags_list):
            page_tags = post_tags_list.find_all('a')

            for tag in page_tags:
                tags.append(Tag(text=tag.string))
                session.bulk_save_objects(tags)
        

        articles.append(
            Article(
                title=entry.title,
                url=entry.comments,
                posted=datetime(*entry.published_parsed[:6]),
                tags=tags
        ))
    
    session.bulk_save_objects(articles)
    session.commit()

    session.close()

    print("\nJob is done")

if __name__ == '__main__':
    main()