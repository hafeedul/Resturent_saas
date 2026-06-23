from flask import render_template, request, redirect, url_for, session, g, flash
from flask import current_app as app
from app import db
from app.models import User, Restaurant, MenuItem

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
        # Extract the subdomain prefix (e.g., 'mario' from 'mario.127.0.0.1:5000' or 'mario.localhost:5000')
        subdomain = host.split('.')[0]
        
        # Find restaurant where domain starts with the subdomain (to handle both 127.0.0.1 and localhost variations)
        g.restaurant = Restaurant.query.filter(Restaurant.domain.like(f"{subdomain}.%")).first()
        
        if g.restaurant:
            # Short-circuit the request for the homepage of the tenant
            if request.path == '/':
                items = MenuItem.query.filter_by(restaurant_id=g.restaurant.id).all()
                return render_template('storefront.html', restaurant=g.restaurant, items=items)
        else:
            return "Restaurant not found on this domain.", 404

@app.route('/')
def home():
    # If we reached here, and it's not main domain, the before_request already handled it
    # unless it wasn't the '/' path, but home is '/'. So this is just for the main domain.
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

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    if request.method == 'POST':
        # Add new menu item
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        
        if name and price:
            try:
                price = float(price)
                new_item = MenuItem(
                    name=name,
                    price=price,
                    description=description,
                    image_url=image_url,
                    restaurant_id=restaurant.id
                )
                db.session.add(new_item)
                db.session.commit()
                flash('Menu item added successfully!')
            except ValueError:
                flash('Price must be a valid number.')
        
        return redirect(url_for('menu'))
        
    items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template('menu.html', items=items)

@app.route('/menu/delete/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    item = db.session.get(MenuItem, item_id)
    if item and item.restaurant_id == restaurant.id:
        db.session.delete(item)
        db.session.commit()
        flash('Menu item deleted.')
        
    return redirect(url_for('menu'))

@app.route('/cart')
def cart():
    # Only available on a tenant domain
    if g.is_main_domain or not g.restaurant:
        return "Not found", 404
        
    cart_items = session.get('cart', {})
    
    # Fetch actual menu items from DB to calculate totals securely
    items_in_cart = []
    total_price = 0.0
    
    for item_id_str, quantity in cart_items.items():
        try:
            item_id = int(item_id_str)
            item = db.session.get(MenuItem, item_id)
            if item and item.restaurant_id == g.restaurant.id:
                line_total = item.price * quantity
                total_price += line_total
                items_in_cart.append({
                    'item': item,
                    'quantity': quantity,
                    'line_total': line_total
                })
        except ValueError:
            continue

    return render_template('cart.html', restaurant=g.restaurant, items_in_cart=items_in_cart, total_price=total_price)

@app.route('/cart/add/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    if g.is_main_domain or not g.restaurant:
        return "Not found", 404
        
    item = db.session.get(MenuItem, item_id)
    if not item or item.restaurant_id != g.restaurant.id:
        return "Item not found", 404
        
    cart = session.get('cart', {})
    
    # Add to cart or increment quantity
    item_id_str = str(item_id)
    if item_id_str in cart:
        cart[item_id_str] += 1
    else:
        cart[item_id_str] = 1
        
    session['cart'] = cart
    flash(f'Added {item.name} to your cart.')
    
    # Redirect back to storefront or cart depending on where they are
    return redirect(request.referrer or url_for('home'))

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if g.is_main_domain or not g.restaurant:
        return "Not found", 404
        
    cart = session.get('cart', {})
    item_id_str = str(item_id)
    
    if item_id_str in cart:
        cart.pop(item_id_str)
        session['cart'] = cart
        
    return redirect(url_for('cart'))

@app.route('/orders')
def orders():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('order.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))
