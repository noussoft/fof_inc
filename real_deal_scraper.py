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
from models import Base, Article, Tag, Author
from db_utils import get_one_or_create

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

def main():

    session = get_session()
    data = feedparser.parse(URL)
    
    for entry in data.entries:

        (article, article_result) = get_one_or_create(
            session,
            Article,
            guid=entry.guid,
            title=entry.title,
            url=entry.comments,
            posted=datetime(*entry.published_parsed[:6])
        )
        session.commit()

        page = get_html(entry.comments)
        parser = BeautifulSoup(page, "html.parser")
        article.tags = get_tags(session, parser)
        article.authors = get_authors(session, parser)
        session.commit()

    session.close()

    print("\nJob is done")

if __name__ == '__main__':
    main()