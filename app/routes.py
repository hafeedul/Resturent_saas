from flask import render_template, request, redirect, url_for, session, g, flash
from flask import current_app as app
from app import db
from app.models import User, Restaurant

# The domain that hosts the main SaaS landing page
# In production this might be 'restostitch.com', locally it's usually '127.0.0.1:5000' or 'localhost:5000'
MAIN_DOMAIN = '127.0.0.1:5000'

@app.before_request
def load_tenant():
    """
    Check the requested domain. If it's not the main domain, 
    look up the Restaurant by domain to serve the custom storefront.
    """
    host = request.host
    g.is_main_domain = (host == MAIN_DOMAIN or host.startswith('localhost'))
    g.restaurant = None
    
    # If it's a tenant domain, fetch the restaurant
    if not g.is_main_domain:
        g.restaurant = Restaurant.query.filter_by(domain=host).first()

@app.route('/')
def home():
    if not g.is_main_domain:
        if g.restaurant:
            return render_template('storefront.html', restaurant=g.restaurant)
        return "Restaurant not found on this domain.", 404
        
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip() if request.form.get('email') else ''
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
            
        flash('Invalid email or password')
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('name')
        restaurant_name = request.form.get('restaurant_name')
        email = request.form.get('email').strip() if request.form.get('email') else ''
        password = request.form.get('password')
        
        # Super simple domain generation for demo (e.g. "The Great Eatery" -> "the-great-eatery.127.0.0.1:5000")
        subdomain_prefix = restaurant_name.lower().replace(' ', '-')
        domain = f"{subdomain_prefix}.127.0.0.1:5000"
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        user = User(name=user_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit() # Commit to get user.id
        
        restaurant = Restaurant(name=restaurant_name, description="Welcome to our restaurant!", domain=domain, owner_id=user.id)
        db.session.add(restaurant)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
        
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = db.session.get(User, session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/menu')
def menu():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('menu.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/orders')
def orders():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('order.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))
