from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date)
    date_of_death = db.Column(db.Date)
    books = db.relationship('Book', backref='author')

    def __repr__(self):
        return f'<Author {self.name}>'

    def __str__(self):
        return f'{self.name}'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20)) #added isbn
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer) #added publication_year
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'

    def __str__(self):
        return f'{self.title}'