from flask import flash, render_template, url_for, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user, login_required
from . import app, db, cache, limiter, qr
from .models import User, Link
import random, string, requests, os


def generate_short_link(length=5):
    chars = string.ascii_letters + string.digits
    short_link = ''.join(random.choice(chars) for _ in range(length))
    return short_link


def generate_qr_code(link, filename):
    qr.add_data(link)
    qr.make(fit=True)
    image = qr.make_image(fill_color="darkmagenta", back_color="#eee")
    image_name = f"qr_code_{filename}.png"
    image_path = f"{app.config['UPLOAD_PATH']}/{image_name}"
    image.save(image_path)
    return image_name


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def error_404(error):
    return render_template('403.html'), 403


@app.route('/', methods=['GET', 'POST'])
@limiter.limit('10/minutes')
def index():
    if request.method == 'POST':
        long_link = request.form['long_link']
        custom_path = request.form['custom_path'] or None
        long_link_exists = Link.query.filter_by(long_link=long_link).first()

        if requests.get(long_link).status_code != 200:
            return render_template('404.html')

        elif long_link_exists:
            flash ('This link has already been shortened.')
            return redirect(url_for('index'))

        elif custom_path:
            path_exists = Link.query.filter_by(custom_path=custom_path).first()
            if path_exists:
                flash ('That custom path is taken. Please try another')
                return redirect(url_for('index'))
            short_link = custom_path

        elif long_link[:4] != 'http':
            long_link = 'http://' + long_link
        
        else:
            while True:
                short_link = generate_short_link()
                short_link_exists = Link.query.filter_by(short_link=short_link).first()
                if not short_link_exists:
                    break
        
        qr_code_path = generate_qr_code(long_link, short_link)
        link = Link(long_link=long_link, short_link=short_link, custom_path=custom_path, 
                    qr_code_path=qr_code_path, user_id=current_user.id)
        db.session.add(link)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/dashboard')
@login_required
@cache.cached(timeout=30)
def dashboard():
    links = Link.query.filter_by(user_id=current_user.id).order_by(Link.created_at.desc()).all()
    host = request.host_url
    return render_template('dashboard.html', links=links, host=host)


@app.route('/history')
@login_required
@cache.cached(timeout=30)
def history():
    links = Link.query.filter_by(user_id=current_user.id).order_by(Link.created_at.desc()).all()
    host = request.host_url
    return render_template('history.html', links=links, host=host)


@app.route('/<short_link>')
@cache.cached(timeout=30)
def redirect_link(short_link):
    link = Link.query.filter_by(short_link=short_link).first()
    if link:
        link.clicks += 1
        db.session.commit()
        return redirect(link.long_link)
    else:
        return render_template('404.html')


@app.route('/<short_link>/delete')
@login_required
def delete(short_link):
    link = Link.query.filter_by(short_link=short_link).first()
    qr_code_path = link.qr_code_path
    full_qr_code_path = f"{app.config['UPLOAD_PATH']}/{qr_code_path}"

    if link:
        os.remove(full_qr_code_path)
        db.session.delete(link)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('404.html')


@app.route('/<short_link>/edit', methods=['GET', 'POST'])
@login_required
@limiter.limit('10/minutes')
def update(short_link):
    link = Link.query.filter_by(short_link=short_link).first()
    host = request.host_url
    if link:
        if request.method == 'POST':
            custom_path = request.form['custom_path']
            if custom_path:
                link_exists = Link.query.filter_by(custom_path=custom_path).first()
                if link_exists:
                    flash ('That custom path already exists. Please try another.')
                    return redirect(url_for('update', short_link=short_link))
                link.custom_path = custom_path
                link.short_link = custom_path
            db.session.commit()
            return redirect(url_for('dashboard'))
        return render_template('edit.html', link=link, host=host)
    return render_template('404.html')


@app.route('/<short_link>/analytics')
@login_required
@cache.cached(timeout=50)
def analytics(short_link):
    link = Link.query.filter_by(short_link=short_link).first()
    host = request.host_url
    if link:
        return render_template('analytics.html', link=link, host=host)
    return render_template('404.html')


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash('This username already exists.')
            return redirect(url_for('register'))

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('This email is already registered.')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        new_user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        flash('You are now signed up.')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash('You are now logged in.')
                return redirect(url_for('index'))
            
            if (user and check_password_hash(user.password_hash, password)) == False:
                flash('Please provide valid credentials.')
                return redirect(url_for('login'))

        else:
            flash('Account not found. Please sign up to continue.')
            return redirect(url_for('register'))
        
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))