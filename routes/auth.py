from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from forms.auth_forms import LoginForm, SignupForm
from models.user import User
from models import db, User

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('chat.index'))
    return render_template('login1.html', form = form)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            name = form.name.data,
            email = form.email.data,
            phone_number = form.phone_number.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User Signed Up')
        return redirect(url_for('auth.login'))
    return render_template('Register.html', form = form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))