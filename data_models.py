from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, ForeignKey

db = SQLAlchemy()

class Author(db.Model):
    author_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    birthdate = Column(String)
    date_of_death = Column(String)

    def __repr__(self):
        return f"name={self.name}, birth_date={self.birthdate}, date_of_death={self.date_of_death}"

    def __str__(self):
        return f"{self.name} ({self.birthdate}-{self.date_of_death})"


class Book(db.Model):
    book_id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(String, nullable=False)
    title = Column(String, nullable=False)
    publication_year = Column(Integer)
    author_id = Column(Integer, ForeignKey("author.author_id"))
    image_url = Column(Text)

    author = relationship("Author", backref="books")

    def __repr__(self):
        return f"title={self.title}, publication_year={self.publication_year}"

    def __str__(self):
        return f"{self.title} ({self.publication_year})"
