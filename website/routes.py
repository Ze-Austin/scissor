from flask import flash, render_template, url_for, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user, login_required
from flask_share import Share
from . import app, db, cache
from .models import User, Link
import random, string


def generate_short_link(length=6):
    chars = string.ascii_letters + string.digits
    short_link = "".join(random.choice(chars) for _ in range(length))
    return short_link


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/signup', methods=['GET', 'POST'])
def register():
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
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        flash('You are now logged in.')
        return redirect(url_for('index'))
    if (user and check_password_hash(user.password_hash, password)) == False:
        flash('Please provide valid credentials.')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))