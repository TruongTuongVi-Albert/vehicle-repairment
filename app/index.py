from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.dao import user_dao

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page - redirect to login if not authenticated"""
    if 'user_id' in session:
        return render_template('home.html')
    return redirect(url_for('main.login'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_dao.auth_user(username, password)
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    logout_user()
    return redirect(url_for('main.login'))
