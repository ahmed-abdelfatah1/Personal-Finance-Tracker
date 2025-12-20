"""Authentication routes - login, register, logout."""

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_user, logout_user, login_required

from ..repositories import UserRepository

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('auth.login'))

    user = UserRepository.get_by_email(email)

    if user and user.check_password(password):
        login_user(user)
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard.dashboard'))

    flash('Invalid email or password', 'error')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    email = request.form.get('email')
    password = request.form.get('password')
    display_name = request.form.get('display_name')

    if not email or not password:
        flash('Email and password are required', 'error')
        return redirect(url_for('auth.register'))

    if UserRepository.email_exists(email):
        flash('Email already registered', 'error')
        return redirect(url_for('auth.register'))

    UserRepository.create(email=email, password=password, display_name=display_name)

    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

