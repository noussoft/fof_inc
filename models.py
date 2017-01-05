from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

from sqlalchemy import (
    Column, Boolean, Integer, Numeric, String, DateTime, Text, Table, ForeignKey
)

tags_articles = Table('tags_articles', Base.metadata,
    Column('tag_id', Integer, ForeignKey('tags.id')),
    Column('article_id', Integer, ForeignKey('articles.id'))
)

authors_articles = Table('authors_articles', Base.metadata,
    Column('author_id', Integer, ForeignKey('authors.id')),
    Column('article_id', Integer, ForeignKey('articles.id')),
    Column('primary_author_yn', Boolean, default=False)
)

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True)
    scraped = Column(DateTime(timezone=True), default=func.now())
    posted = Column(DateTime(timezone=True))
    publication_id = Column(Integer)
    url = Column(String(255))
    photo1_url = Column(String(255))

    tags = relationship("Tag",
                    secondary=tags_articles,
                    backref="articles")

    authors = relationship("Author",
                    secondary=authors_articles,
                    backref="articles")

class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    first = Column(String(32), index=True)
    last = Column(String(32), index=True)
    email = Column(String(255), index=True)
    twitter = Column(String(255))
    facebook = Column(String(255))
    website = Column(String(255))
    articles_page = Column(String(255))
    bio = Column(Text)

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    text = Column(String(32))