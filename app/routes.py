from flask import render_template
from flask import current_app as app

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/orders')
def orders():
    return render_template('order.html')
