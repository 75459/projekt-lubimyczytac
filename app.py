import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
import time
from flask import request, jsonify

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'develope-super-secret-key-75459')

db = SQLAlchemy(app)

# ==========================================
# MODELE BAZODANOWE I PROCESY GLOBALNE
# ==========================================

class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, nullable=True) # Zgodnie z wytycznymi pole zostaje, mimo braku w schemacie SQL
    books = db.relationship('Book', backref='author', lazy=True)

class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    desc = db.Column(db.Text, default="Brak opisu.")
    books = db.relationship('Book', backref='genre', lazy=True)

class PubHouse(db.Model):
    __tablename__ = 'pub_house'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    mail = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    webpage = db.Column(db.String(255), nullable=False)
    books = db.relationship('Book', backref='publisher', lazy=True)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    desc = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(255), nullable=False)
    pub_date = db.Column(db.DateTime(timezone=True), nullable=False)
    pages_number = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String(255), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    pub_house_id = db.Column(db.Integer, db.ForeignKey('pub_house.id'), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)

# Mapowanie istniejącej w bazie tabeli asocjacyjnej
read_books_association = db.Table('read_books',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    extend_existing=True
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    mail = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    temp_code = db.Column(db.String(6), nullable=True)
    admin = db.Column(db.Integer, default=0, nullable=False)
    
    # Odczyt relacji książek
    read_books = db.relationship('Book', secondary=read_books_association, lazy='subquery',
        backref=db.backref('readers', lazy=True))

def generate_mixed_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

@app.route('/profpic.png')
def serve_profpic():
    return send_from_directory(os.getcwd(), 'profpic.png')

last_requests = {}

def rate_limited(seconds=1):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Używamy IP użytkownika jako klucza
            ip = request.remote_addr
            key = f"{f.__name__}_{ip}"
            now = time.time()
            
            # Sprawdzenie różnicy czasu
            if now - last_requests.get(key, 0) < seconds:
                return jsonify({"error": "Zbyt częste zapytanie. Poczekaj chwilę."}), 429
            
            # Aktualizacja czasu
            last_requests[key] = now
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.context_processor
def inject_global_data():
    current_user = None
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
    return dict(
        global_genres=Genre.query.all(),
        global_authors=Author.query.all(),
        global_publishers=PubHouse.query.all(),
        current_user=current_user
    )
# ==========================================
# ROUTING GŁÓWNY I API FRONTENDU
# ==========================================

@app.route('/')
def index():
    all_books = Book.query.order_by(Book.id.desc()).all()
    return render_template('index.html', books=all_books)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book.html', book=book)

@app.route('/author/<int:author_id>')
def author_detail(author_id):
    author = Author.query.get_or_404(author_id)
    return render_template('author.html', author=author)

@app.route('/pubhouse/<int:pub_id>')
def publisher_detail(pub_id):
    pub = PubHouse.query.get_or_404(pub_id)
    return render_template('publisher.html', publisher=pub)

@app.route('/genre/<int:genre_id>')
def genre_detail(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    return render_template('genre.html', genre=genre)

@app.route('/read_books')
def read_books_page():
    if 'user_id' not in session:
        return redirect(url_for('account_page'))
    user = User.query.get(session['user_id'])
    return render_template('read_books.html', books=user.read_books)

@app.route('/api/toggle_read/<int:book_id>', methods=['POST'])
@rate_limited(seconds=1)
def toggle_read(book_id):
    if 'user_id' not in session: 
        return jsonify({'success': False, 'message': 'Zaloguj się'}), 401
    
    user = User.query.get(session['user_id'])
    book = Book.query.get_or_404(book_id)

    if book in user.read_books:
        user.read_books.remove(book)
        status = 'removed'
    else:
        user.read_books.append(book)
        status = 'added'
        
    db.session.commit()
    return jsonify({'success': True, 'status': status})

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/account')
def account_page():
    return render_template('account.html')

@app.route('/profile')
def profile_page():
    if 'user_id' not in session:
        return redirect(url_for('account_page'))
    return render_template('profile.html')

@app.route('/regulamin')
def regulamin_page():
    return render_template('regulamin.html')

@app.route('/search')
def search_results():
    phrase = request.args.get('fraza', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Book.query.join(Author, isouter=True).filter(
        db.or_(
            Book.title.ilike(f"%{phrase}%"),
            Author.name.ilike(f"%{phrase}%"),
            Author.surname.ilike(f"%{phrase}%")
        )
    )
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('index.html', books=pagination.items, phrase=phrase, pagination=pagination)

@app.route('/api/check_login')
def check_login():
    val = request.args.get('login', '').strip()
    if not val: return jsonify(exists=False)
    exists = User.query.filter(db.func.lower(User.login) == val.lower()).first() is not None
    return jsonify(exists=exists)

@app.route('/api/check_username')
def check_username():
    val = request.args.get('username', '').strip()
    if not val: return jsonify(exists=False)
    exists = User.query.filter(db.func.lower(User.username) == val.lower()).first() is not None
    return jsonify(exists=exists)

@app.route('/api/check_email')
def check_email():
    val = request.args.get('mail', '').strip()
    if not val: return jsonify(exists=False)
    exists = User.query.filter(db.func.lower(User.mail) == val.lower()).first() is not None
    return jsonify(exists=exists)

@app.route('/api/search_suggest')
def search_suggest():
    query_param = request.args.get('q', '').strip()
    if not query_param: return jsonify([])
    results = []
    matched_books = Book.query.join(Author, isouter=True).filter(
        db.or_(
            Book.title.ilike(f"%{query_param}%"),
            Author.name.ilike(f"%{query_param}%"),
            Author.surname.ilike(f"%{query_param}%")
        )
    ).limit(4).all()
    for b in matched_books:
        author_str = f"{b.author.name} {b.author.surname}" if b.author else "Nieznany autor"
        results.append({"text": f"<strong>{b.title}</strong> - {author_str}", "url": f"/book/{b.id}"})
    return jsonify(results[:10])

@app.route('/api/check_isbn')
def check_isbn():
    isbn_raw = request.args.get('isbn', '').strip()
    isbn_clean = isbn_raw.replace('-', '')
    if not isbn_clean: return jsonify({"exists": False})
    books = Book.query.all()
    for b in books:
        if b.isbn and b.isbn.replace('-', '') == isbn_clean:
            return jsonify({"exists": True, "id": b.id, "title": b.title})
    return jsonify({"exists": False})

@app.route('/api/check_author')
def check_author():
    name = request.args.get('name', '').strip().lower()
    surname = request.args.get('surname', '').strip().lower()
    authors = Author.query.all()
    for a in authors:
        if a.name.strip().lower() == name and a.surname.strip().lower() == surname:
            return jsonify({"exists": True})
    return jsonify({"exists": False})

@app.route('/api/check_publisher')
def check_publisher():
    name = request.args.get('name', '').strip().lower()
    publishers = PubHouse.query.all()
    for p in publishers:
        if p.name.strip().lower() == name: return jsonify({"exists": True})
    return jsonify({"exists": False})

@app.route('/api/check_genre')
def check_genre():
    name = request.args.get('name', '').strip().lower()
    genres = Genre.query.all()
    for g in genres:
        if g.name.strip().lower() == name: return jsonify({"exists": True})
    return jsonify({"exists": False})

@app.route('/api/random_isbn')
def random_isbn():
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2:
        return jsonify({"success": False, "message": "Brak uprawnień."}), 403

    popular_english_pool = [
        '9780439139595', '9780451524935', '9780061120084', '9780743273565', '9780345339683'
    ]
    try:
        existing_isbns = {b.isbn.replace('-', '').strip() for b in Book.query.all() if b.isbn}
        available_pool = [isbn for isbn in popular_english_pool if isbn not in existing_isbns]
        if available_pool:
            return jsonify({"isbn": random.choice(available_pool), "success": True})
        return jsonify({"isbn": random.choice(popular_english_pool), "success": True})
    except Exception:
        return jsonify({"isbn": random.choice(popular_english_pool), "success": True})
    # ==========================================
# SYSTEM AUTORYZACJI, KONTA I SESJE
# ==========================================

@app.route('/register', methods=['POST'])
@rate_limited(seconds=1)
def register():
    login = request.form.get('login', '').strip()
    username = request.form.get('username', '').strip()
    mail = request.form.get('mail', '').strip()
    password = request.form.get('password')

    if User.query.filter((User.login == login) | (User.mail == mail) | (User.username == username)).first():
        return jsonify({"success": False, "message": "Dane są już zajęte!"}), 400

    code = generate_mixed_code()
    hashed_pw = generate_password_hash(password, method='scrypt')

    new_user = User(login=login, username=username, mail=mail, password=hashed_pw, is_active=False, temp_code=code)
    db.session.add(new_user)
    db.session.commit()

    session['verify_email'] = mail
    session['verify_purpose'] = 'register'
    print(f"[DEMO SANDBOX] Kod rejestracji dla {mail}: {code}")
    return jsonify({"success": True})

@app.route('/reset_password_request', methods=['POST'])
@rate_limited(seconds=1)
def reset_password_request():
    mail = request.form.get('mail', '').strip()
    user = User.query.filter_by(mail=mail).first()
    
    if not user:
        return jsonify({"success": False, "message": "Nie znaleziono takiego adresu e-mail!"}), 404

    code = generate_mixed_code()
    user.temp_code = code
    db.session.commit()

    session['verify_email'] = mail
    session['verify_purpose'] = 'reset'
    print(f"[DEMO SANDBOX] Kod resetu dla {mail}: {code}")
    return jsonify({"success": True})

@app.route('/verify_code', methods=['POST'])
@rate_limited(seconds=1)
def verify_code():
    code = request.form.get('full_code', '').strip().upper()
    mail = session.get('verify_email')
    purpose = session.get('verify_purpose', 'register')

    user = User.query.filter_by(mail=mail).first()
    
    # Weryfikujemy tylko czy użytkownik istnieje w sesji, żeby system nie wybuchł
    if not user:
        return jsonify({"success": False, "message": "Błąd sesji: Nie znaleziono użytkownika!"}), 400

    # SANDBOX BYPASS: Usunięto warunek "user.temp_code != code"
    # System przyjmuje i akceptuje cokolwiek wpisane w pola na froncie

    if purpose == 'register':
        user.is_active = True
        user.temp_code = None
        db.session.commit()
        session['user_id'] = user.id
        return jsonify({"success": True, "target": "home"})
        
    return jsonify({"success": True, "target": "new_password"})

@app.route('/reset_password_final', methods=['POST'])
@rate_limited(seconds=1)
def reset_password_final():
    password = request.form.get('password')
    mail = session.get('verify_email')
    user = User.query.filter_by(mail=mail).first()
    if not user:
        return jsonify({"success": False, "message": "Błąd sesji."}), 400

    user.password = generate_password_hash(password, method='scrypt')
    user.temp_code = None
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({"success": True})

@app.route('/login', methods=['POST'])
def login():
    identity = request.form.get('identity', '').strip()
    password = request.form.get('password', '')
    user = User.query.filter((User.login == identity) | (User.username == identity) | (User.mail == identity)).first()

    if user and check_password_hash(user.password, password):
        if not user.is_active:
            session['verify_email'] = user.mail
            session['verify_purpose'] = 'register'
            return jsonify({"success": False, "requires_verification": True, "mail": user.mail})
        session['user_id'] = user.id
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Nieprawidłowy identyfikator lub hasło!"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/update_username', methods=['POST'])
@rate_limited(seconds=1)
def update_username():
    if 'user_id' not in session: return jsonify({"success": False}), 401
    new_username = request.form.get('username', '').strip()
    exists = User.query.filter(User.id != session['user_id'], db.func.lower(User.username) == new_username.lower()).first()
    if exists: return jsonify({"success": False, "message": "Ten pseudonim jest już zajęty!"}), 400
    user = User.query.get(session['user_id'])
    user.username = new_username
    db.session.commit()
    return jsonify({"success": True})

@app.route('/update_password', methods=['POST'])
@rate_limited(seconds=1)
def update_password():
    if 'user_id' not in session: return jsonify({"success": False}), 401
    password = request.form.get('password')
    user = User.query.get(session['user_id'])
    user.password = generate_password_hash(password, method='scrypt')
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/resend_verification_code')
@rate_limited(seconds=1)
def resend_verification_code():
    mail = request.args.get('mail', '').strip()
    user = User.query.filter_by(mail=mail).first()
    if not user:
        return jsonify({"success": False, "message": "Nie znaleziono użytkownika."}), 404
    
    code = generate_mixed_code()
    user.temp_code = code
    db.session.commit()
    print(f"[DEMO SANDBOX] Ponowne wysłanie kodu dla {mail}: {code}")
    return jsonify({"success": True})
# ==========================================
# AKCJE INTEGRACYJNE Z BAZĄ DANYCH (CRUD - ADMIN = 2)
# ==========================================

@app.route('/add_book', methods=['POST'])
@rate_limited(seconds=1)
def add_book():
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2:
        return "Brak uprawnień.", 403

    author_id_raw = request.form.get('author_id')
    if author_id_raw and author_id_raw.startswith("NEW:"):
        name_parts = author_id_raw.replace("NEW:", "").strip().rsplit(' ', 1)
        new_author = Author(name=name_parts[0], surname=name_parts[1] if len(name_parts) > 1 else "Nieznane")
        db.session.add(new_author)
        db.session.commit()
        author_id = new_author.id
    else:
        author_id = int(author_id_raw) if author_id_raw else None

    pub_id_raw = request.form.get('pub_house_id')
    if pub_id_raw and pub_id_raw.startswith("NEW:"):
        new_pub = PubHouse(
            name=pub_id_raw.replace("NEW:", "").strip(), 
            address="Brak", 
            mail="brak@danych.pl", 
            phone="brak", 
            webpage="brak"
        )
        db.session.add(new_pub)
        db.session.commit()
        pub_house_id = new_pub.id
    else:
        pub_house_id = int(pub_id_raw) if pub_id_raw else None

    genre_id_raw = request.form.get('genre_id')
    if genre_id_raw and genre_id_raw.startswith("NEW:"):
        new_genre = Genre(name=genre_id_raw.replace("NEW:", "").strip(), desc="Brak opisu.")
        db.session.add(new_genre)
        db.session.commit()
        genre_id = new_genre.id
    else:
        genre_id = int(genre_id_raw) if genre_id_raw else None

    pub_date_raw = request.form.get('pub_date')
    pub_date = datetime.strptime(pub_date_raw, '%Y-%m-%d') if pub_date_raw else None
    
    desc_raw = request.form.get('desc') or "Brak opisu"
    if len(desc_raw) > 255:
        desc_raw = desc_raw[:252] + "..."

    new_book = Book(
        title=request.form.get('title') or "Nieznany tytuł", 
        isbn=request.form.get('isbn') or "Brak",
        genre_id=genre_id, 
        author_id=author_id, 
        pub_house_id=pub_house_id,
        desc=desc_raw, 
        pub_date=pub_date,
        pages_number=int(request.form.get('pages_number') or 1), 
        language=request.form.get('language') or "nieznany"
    )
    db.session.add(new_book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit_book/<int:book_id>', methods=['POST'])
@rate_limited(seconds=1)
def edit_book(book_id):
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2:
        return "Brak uprawnień.", 403

    book = Book.query.get_or_404(book_id)
    try:
        book.title = request.form.get('title') or "Nieznany tytuł"
        
        desc_raw = request.form.get('desc') or "Brak opisu"
        if len(desc_raw) > 255:
            desc_raw = desc_raw[:252] + "..."
        book.desc = desc_raw
        
        book.pages_number = int(request.form.get('pages_number') or 1)
        book.language = request.form.get('language') or "nieznany"
        
        if request.form.get('author_id'): book.author_id = int(request.form.get('author_id'))
        if request.form.get('pub_house_id'): book.pub_house_id = int(request.form.get('pub_house_id'))
        if request.form.get('genre_id'): book.genre_id = int(request.form.get('genre_id'))
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for('book_detail', book_id=book.id))

@app.route('/delete_book/<int:book_id>', methods=['POST'])
@rate_limited(seconds=1)
def delete_book(book_id):
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2: 
        return "Brak uprawnień.", 403
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_author', methods=['POST'])
@rate_limited(seconds=1)
def add_author():
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2: 
        return "Brak uprawnień.", 403
        
    bio_raw = request.form.get('bio')
    if bio_raw and len(bio_raw) > 255:
        bio_raw = bio_raw[:252] + "..."
        
    new_author = Author(
        name=request.form.get('name') or "Nieznane", 
        surname=request.form.get('surname') or "Nieznane", 
        bio=bio_raw
    )
    db.session.add(new_author)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_publisher', methods=['POST'])
@rate_limited(seconds=1)
def add_publisher():
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2: 
        return "Brak uprawnień.", 403
        
    new_pub = PubHouse(
        name=request.form.get('name') or "Nieznane", 
        address=request.form.get('address') or "Brak",
        mail=request.form.get('email') or "brak@danych.pl",
        phone=request.form.get('phone') or "brak",
        webpage=request.form.get('website') or "brak"
    )
    db.session.add(new_pub)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_genre', methods=['POST'])
@rate_limited(seconds=1)
def add_genre():
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2: 
        return "Brak uprawnień.", 403
        
    desc_raw = request.form.get('desc') or "Brak opisu."
    if len(desc_raw) > 255:
        desc_raw = desc_raw[:252] + "..."
        
    new_genre = Genre(
        name=request.form.get('name') or "Nieznane",
        desc=desc_raw # ZAPIS OPISU DO BAZY
    )
    db.session.add(new_genre)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_author/<int:author_id>', methods=['POST'])
@rate_limited(seconds=1)
def delete_author(author_id):
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2:
        return "Brak uprawnień administratora.", 403
    if author_id == 1:
        return "Krytyczny błąd: Nie można usunąć domyślnej pozycji systemowej 'Nieznane'!", 400

    mode = request.form.get('mode')
    if mode == 'cascade':
        Book.query.filter_by(author_id=author_id).delete()
    else:
        Book.query.filter_by(author_id=author_id).update({Book.author_id: 1})

    author = Author.query.get_or_404(author_id)
    db.session.delete(author)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_genre/<int:genre_id>', methods=['POST'])
@rate_limited(seconds=1)
def delete_genre(genre_id):
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2:
        return "Brak uprawnień administratora.", 403
    if genre_id == 1:
        return "Krytyczny błąd: Nie można usunąć domyślnej pozycji systemowej 'Nieznane'!", 400

    mode = request.form.get('mode')
    if mode == 'cascade':
        Book.query.filter_by(genre_id=genre_id).delete()
    else:
        Book.query.filter_by(genre_id=genre_id).update({Book.genre_id: 1})

    genre = Genre.query.get_or_404(genre_id)
    db.session.delete(genre)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_publisher/<int:pub_id>', methods=['POST'])
@rate_limited(seconds=1)
def delete_publisher(pub_id):
    if 'user_id' not in session or User.query.get(session['user_id']).admin != 2:
        return "Brak uprawnień administratora.", 403
    if pub_id == 1:
        return "Krytyczny błąd: Nie można usunąć domyślnej pozycji systemowej 'Nieznane'!", 400

    mode = request.form.get('mode')
    if mode == 'cascade':
        Book.query.filter_by(pub_house_id=pub_id).delete()
    else:
        Book.query.filter_by(pub_house_id=pub_id).update({Book.pub_house_id: 1})

    pub = PubHouse.query.get_or_404(pub_id)
    db.session.delete(pub)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
