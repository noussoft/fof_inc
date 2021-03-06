import os
import re
import sys
import urllib.parse
from urllib.request import urlretrieve, HTTPError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy_utils.functions import database_exists, create_database

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool

from bs4 import BeautifulSoup

from settings import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST
from models import Base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'images')

def get_session():
    engine = create_engine(
        'mysql://{}:{}@{}/{}?charset=utf8'.format(DB_USER, DB_PASSWORD, DB_HOST, DB_NAME),
        poolclass=NullPool)
    Session = sessionmaker(bind=engine)
    session = Session()

    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.create_all(engine)

    return session

def get_one_or_create(session,
                      model,
                      create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), True
    except NoResultFound:
        kwargs.update(create_method_kwargs or {})
        try:
            with session.begin_nested():
                created = getattr(model, create_method, model)(**kwargs)
                session.add(created)
            return created, False
        except IntegrityError:
            return session.query(model).filter_by(**kwargs).one(), True

def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7f]', r'_', text)

def prepare_url(url):
    url = urllib.parse.urlsplit(url)
    url = list(url)
    url[2] = urllib.parse.quote(url[2])
    return urllib.parse.urlunsplit(url)

def save_image(url):
    file_to_save = remove_non_ascii(url.split('/')[-1])
    full_path_name = os.path.join(OUTPUT_DIR, file_to_save)

    if not os.path.isfile(full_path_name):
        try:
            urlretrieve(prepare_url(url), full_path_name)
        except HTTPError:
            pass
    return file_to_save

def get_url_from_more_link(text, link_text='[more]'):
    parser = BeautifulSoup(text, "html.parser")
    ahrefs = [url['href'] for url in parser.find_all('a') if url.text.lower() == link_text]
    try:
      return ahrefs[0]
    except IndexError:
      return None
