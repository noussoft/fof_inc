import os
import re
import urllib.parse
from urllib.request import urlretrieve
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'images')

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
    print(url)
    file_to_save = remove_non_ascii(url.split('/')[-1])
    urlretrieve(prepare_url(url), os.path.join(OUTPUT_DIR, file_to_save))
    return file_to_save