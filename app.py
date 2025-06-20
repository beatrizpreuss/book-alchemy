import os
import requests
from flask import Flask, render_template, request, redirect, url_for
from data_models import db, Author, Book
from sqlalchemy.orm import joinedload

app = Flask(__name__)

# Build absolute path to database
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'data', 'library.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

os.makedirs(os.path.join(basedir, 'data'), exist_ok=True)

db.init_app(app)

# Only needed once to create tables
# with app.app_context():
#   db.create_all()


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """
    Handle the addition of a new author via a web form.

    If the request method is POST, retrieves author data from the submitted form,
    creates a new Author instance, and saves it to the database. On success, it returns
    a confirmation message.

    If the request method is GET, renders the form to add a new author.

    Returns:
        str: Success message when a new author is added via POST.
        Response: Rendered HTML template for the add author form on GET.
    """
    if request.method == 'POST':
        name = request.form["name"]
        birthdate = request.form["birthdate"]
        date_of_death = request.form["date_of_death"]

        new_author = Author(
            name=name,
            birthdate=birthdate,
            date_of_death=date_of_death
        )
        db.session.add(new_author)
        db.session.commit()
        return "New author successfully added to database"

    return render_template('add_author.html')


def fetch_book_image(title, isbn):
    """
    Fetch the thumbnail image URL for a book using the Google Books API.

    Combines the book title and ISBN into a search query, sends a request to the
    Google Books API, and attempts to retrieve the thumbnail image URL from the
    first search result.

    Args:
        title (str): The title of the book.
        isbn (str): The ISBN of the book.

    Returns:
        str: The URL of the book's thumbnail image if found, otherwise an empty string.
    """
    try:
        query = f"{title} {isbn}"
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
        response = requests.get(url)
        data = response.json()

        if "items" in data:
            volume_info = data["items"][0]["volumeInfo"]
            return volume_info.get("imageLinks", {}).get("thumbnail", "")
    except Exception as e:
        print("Error fetching image:", e)

    return ""


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """
    Handle the addition of a new book to the database.

    For GET requests, renders a form allowing users to input book information
    and select an author from the existing list.

    For POST requests, receives form data for a new book, fetches its image
    using the Google Books API, creates a new Book instance, and commits it
    to the database.

    Returns:
        str: A success message if the book is added (on POST),
        Response: the rendered add_book.html template with the list of authors (on GET).
    """
    if request.method == 'POST':
        title = request.form["title"]
        isbn = request.form["isbn"]
        publication_year = request.form["publication_year"]
        author_id = request.form["author_id"]

        image_url = fetch_book_image(title, isbn)

        new_book = Book(
            title=title,
            isbn=isbn,
            publication_year=publication_year,
            author_id=author_id,
            image_url=image_url
        )
        db.session.add(new_book)
        db.session.commit()
        return "New book successfully added to database"

    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)


@app.route('/', methods=['GET', 'POST'])
def home():
    """
    Display the list of books or search for books by title.

    On GET retrieves and displays all books.
    On POST, searches for books with titles matching the search query (case-insensitive).
    If no books are found, displays a "No books found" message.

    Returns:
        str: An informational message if no books are found.
        Response: Rendered 'home.html' template with a list of Book objects matching the query or all books.
    """
    if request.method == "POST":
        search = request.form["search"]
        books = Book.query.filter(Book.title.ilike(f"%{search}%")).all()
        if len(books) == 0:
            return "No books found"
        return render_template('home.html', books=books)

    books = Book.query.all()
    return render_template('home.html', books=books)


@app.route('/sort_by_title', methods=['GET'])
def sort_by_title():
    """
    Retrieve all books sorted alphabetically by their title and render them on the home page.

    Returns:
        Response: Rendered 'home.html' template with a list of Book objects sorted by title.
    """
    books = Book.query.order_by(Book.title).all()
    return render_template('home.html', books=books)


@app.route('/sort_by_author', methods=['GET'])
def sort_by_author():
    """
    Retrieve all books sorted alphabetically by their author's name and render them on the home page.

    Returns:
        Response: Rendered 'home.html' template with a list of Book objects sorted by the author's name.
    """
    books = Book.query.join(Author).order_by(Author.name).options(joinedload(Book.author)).all() #joinedload ensures the authors are loaded alongside the books efficiently when you sort by author’s name
    return render_template('home.html', books=books)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete(book_id):
    """
    Deletes a book by its ID and removes any authors without remaining books.

    Args:
        book_id (int): The ID of the book to delete.

    Returns:
        Response: Redirects to the home page if the deletion is successful.
        str: Error message with 404 status code if the book is not found.
    """
    book = Book.query.get(book_id)
    if book:
        db.session.delete(book)
        db.session.commit()
        print(f"Book with ID {book_id} deleted.")

        # Check for authors without books
        authors_ids_with_books = db.session.query(Book.author_id).distinct() # query only the author_id in the Book table
        authors_ids_without_books = Author.query.filter(~Author.author_id.in_(authors_ids_with_books)) # query the whole Author table because e want to delete the whole author row

        authors_ids_without_books.delete(synchronize_session=False)
        db.session.commit()


        return redirect(url_for('home'))
    else:
        return f"No book found with ID {book_id}", 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
