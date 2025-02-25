from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from data_models import db, Author, Book
import os
import requests
from datetime import date

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data', 'library.sqlite')
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

cover_image_cache = {}

def get_book_cover(isbn):
    if isbn in cover_image_cache:
        return cover_image_cache[isbn]
    if not isbn:
        return None
    try:
        url = f'https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg'
        response = requests.get(url)
        if response.status_code == 200:
            cover_image_cache[isbn] = url
            return url
        else:
            cover_image_cache[isbn] = None
            return None
    except requests.exceptions.RequestException:
        cover_image_cache[isbn] = None
        return None

def seed_database():
    with app.app_context():
        authors_data = [
            {"name": "J.R.R. Tolkien", "birth_date": date(1892, 1, 3), "date_of_death": date(1973, 9, 2)},
            {"name": "George Orwell", "birth_date": date(1903, 6, 25), "date_of_death": date(1950, 1, 21)},
            {"name": "Jane Austen", "birth_date": date(1775, 12, 16), "date_of_death": date(1817, 7, 18)},
            {"name": "Stephen King", "birth_date": date(1947, 9, 21), "date_of_death": None},
            {"name": "Agatha Christie", "birth_date": date(1890, 9, 15), "date_of_death": date(1976, 1, 12)},
            {"name": "Ernest Hemingway", "birth_date": date(1899, 7, 21), "date_of_death": date(1961, 7, 2)},
            {"name": "Harper Lee", "birth_date": date(1926, 4, 28), "date_of_death": date(2016, 2, 19)},
            {"name": "Gabriel García Márquez", "birth_date": date(1927, 3, 6), "date_of_death": date(2014, 4, 17)},
            {"name": "Isaac Asimov", "birth_date": date(1920, 1, 2), "date_of_death": date(1992, 4, 6)},
            {"name": "Margaret Atwood", "birth_date": date(1939, 11, 18), "date_of_death": None},
        ]
        for author_data in authors_data:
            author = Author(**author_data)
            db.session.add(author)
        books_data = [
            {"isbn": "9780618260300", "title": "The Lord of the Rings", "publication_year": 1954, "author_id": 1},
            {"isbn": "9780451524935", "title": "1984", "publication_year": 1949, "author_id": 2},
            {"isbn": "9780141439518", "title": "Pride and Prejudice", "publication_year": 1813, "author_id": 3},
            {"isbn": "9781501142976", "title": "It", "publication_year": 1986, "author_id": 4},
            {"isbn": "9780062073484", "title": "Murder on the Orient Express", "publication_year": 1934, "author_id": 5},
            {"isbn": "9780684801223", "title": "The Old Man and the Sea", "publication_year": 1952, "author_id": 6},
            {"isbn": "9780061120084", "title": "To Kill a Mockingbird", "publication_year": 1960, "author_id": 7},
            {"isbn": "9780061120084", "title": "One Hundred Years of Solitude", "publication_year": 1967, "author_id": 8},
            {"isbn": "9780553293357", "title": "Foundation", "publication_year": 1951, "author_id": 9},
            {"isbn": "9780385490813", "title": "The Handmaid's Tale", "publication_year": 1985, "author_id": 10},
        ]
        for book_data in books_data:
            book = Book(**book_data)
            db.session.add(book)
        db.session.commit()

if not os.path.exists(os.path.join(basedir, 'data', 'library.sqlite')):
    with app.app_context():
        db.create_all()
    with app.app_context():
        if not Book.query.first():
            seed_database()

@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        name = request.form['name']
        birth_date = request.form['birth_date']
        date_of_death = request.form['date_of_death']
        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)
        db.session.add(new_author)
        db.session.commit()
        flash('Author added successfully!', 'success')
        return redirect(url_for('add_author'))
    return render_template('add_author.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']
        new_book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('add_book'))
    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)

@app.route('/', methods=['GET', 'POST'])
@app.route('/sort', methods=['GET', 'POST'])
def index():
    sort_by = request.args.get('sort_by')
    search_query = request.form.get('search_query')
    if search_query:
        books = Book.query.filter(Book.title.like(f"%{search_query}%")).all()
    elif sort_by == 'title':
        books = Book.query.order_by(Book.title).all()
    elif sort_by == 'author':
        books = Book.query.join(Author).order_by(Author.name).all()
    else:
        books = Book.query.all()
    for book in books:
        book.cover_image = get_book_cover(book.isbn)
    return render_template('index.html', books=books, search_query=search_query)

@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    author_id = book.author_id
    db.session.delete(book)
    db.session.commit()

    # Check if the author has any other books
    other_books = Book.query.filter_by(author_id=author_id).first()
    if not other_books:
        author = Author.query.get_or_404(author_id)
        db.session.delete(author)
        db.session.commit()

    flash('Book deleted successfully!', 'success')
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(debug=True, port=5002)