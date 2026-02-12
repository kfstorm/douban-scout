from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    douban_id = Column(String(16), unique=True, nullable=False, index=True)
    imdb_id = Column(String(16), nullable=True)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True, index=True)
    rating = Column(Float, nullable=True, index=True)
    rating_count = Column(Integer, default=0, index=True)
    type = Column(String(16), nullable=False, index=True)
    poster_url = Column(Text, nullable=True)
    douban_url = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)

    genres = relationship(
        "MovieGenre", back_populates="movie", cascade="all, delete-orphan"
    )


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id = Column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    genre = Column(String(32), primary_key=True, index=True)

    movie = relationship("Movie", back_populates="genres")


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/movies.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
