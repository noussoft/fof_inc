from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

from sqlalchemy import (
    Column, Boolean, Integer, Numeric, String, DateTime,
    LargeBinary, Text, Table, ForeignKey,
)

tags_articles = Table('tags_articles', Base.metadata,
    Column('tag_id', Integer, ForeignKey('tags.id')),
    Column('article_id', Integer, ForeignKey('articles.id'))
)

authors_articles = Table('authors_articles', Base.metadata,
    Column('author_id', Integer, ForeignKey('authors.id')),
    Column('article_id', Integer, ForeignKey('articles.id')),
    Column('primary_author_yn', Boolean, default=True)
)

class Publication(Base):
    __tablename__ = 'publications'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True, nullable=False)
    url = Column(String(255))
    mobile_url = Column(String(255))
    rss_url = Column(String(255))

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    guid = Column(String(255), index=True, unique=True, nullable=False)
    title = Column(String(255), index=True, nullable=False)
    subtitle = Column(String(255), index=True)
    scraped = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    posted = Column(DateTime(timezone=True), index=True)
    body = Column(Text)
    publication_id = Column(Integer, ForeignKey('publications.id'))
    url = Column(String(255))
    photo1_url = Column(String(255))
    photo1_filename = Column(String(255))
    photo2_url = Column(String(255))
    photo2_filename = Column(String(255))

    tags = relationship("Tag",
                    secondary=tags_articles,
                    backref="articles")

    authors = relationship("Author",
                    secondary=authors_articles,
                    backref="articles")

    publication = relationship("Publication", backref="articles")

    def __repr__(self):
        return "{} - {}".format(self.guid, self.title)

class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    first = Column(String(32), index=True, nullable=False)
    last = Column(String(32), index=True)
    email = Column(String(255), index=True)
    twitter = Column(String(255))
    facebook = Column(String(255))
    website = Column(String(255))
    articles_page = Column(String(255))
    bio = Column(Text)

    def __repr__(self):
        return " ".join([self.first, self.last])

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    text = Column(String(255), unique=True, nullable=False)

    def __repr__(self):
        return self.text
