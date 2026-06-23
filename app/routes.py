from flask import render_template, request, redirect, url_for, session, g, flash
from flask import current_app as app
from app import db
from app.models import User, Restaurant, MenuItem, Order, HeroSlide

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
                slides = HeroSlide.query.filter_by(restaurant_id=g.restaurant.id).all()
                return render_template('storefront.html', restaurant=g.restaurant, items=items, slides=slides)
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
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    # Calculate Basic Analytics
    total_orders = Order.query.filter_by(restaurant_id=restaurant.id).count()
    menu_items_count = MenuItem.query.filter_by(restaurant_id=restaurant.id).count()
    
    # Get 5 most recent orders
    recent_orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           user=user, 
                           restaurant=restaurant, 
                           total_orders=total_orders, 
                           menu_items_count=menu_items_count, 
                           recent_orders=recent_orders)

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
        category = request.form.get('category', 'Main')
        
        if name and price:
            try:
                price = float(price)
                new_item = MenuItem(
                    name=name,
                    price=price,
                    description=description,
                    image_url=image_url,
                    category=category,
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

@app.route('/checkout', methods=['POST'])
def checkout():
    if g.is_main_domain or not g.restaurant:
        return "Not found", 404
        
    customer_name = request.form.get('customer_name', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    dining_option = request.form.get('dining_option', 'Delivery')
    delivery_address = request.form.get('delivery_address', '').strip()
    table_number = request.form.get('table_number', '').strip()
    special_instructions = request.form.get('special_instructions', '').strip()
    
    if not customer_name or not customer_phone:
        flash("Please provide your name and phone number.")
        return redirect(url_for('cart'))
        
    if dining_option == 'Delivery' and not delivery_address:
        flash("Please provide a delivery address.")
        return redirect(url_for('cart'))
        
    if dining_option == 'Dine-In' and not table_number:
        flash("Please provide your table number.")
        return redirect(url_for('cart'))
        
    cart_items = session.get('cart', {})
    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for('cart'))
        
    # Calculate total and build items summary
    total_price = 0.0
    items_summary_list = []
    
    for item_id_str, quantity in cart_items.items():
        try:
            item_id = int(item_id_str)
            item = db.session.get(MenuItem, item_id)
            if item and item.restaurant_id == g.restaurant.id:
                line_total = item.price * quantity
                total_price += line_total
                items_summary_list.append(f"{quantity}x {item.name}")
        except ValueError:
            continue
            
    if total_price == 0:
        return redirect(url_for('cart'))
        
    # Create the Order
    # Build a JSON-like structure for the items column to store raw cart
    raw_items = []
    for item_id_str, qty in cart_items.items():
        try:
            it = db.session.get(MenuItem, int(item_id_str))
            if it:
                raw_items.append({"name": it.name, "price": it.price, "quantity": qty})
        except:
            pass

    new_order = Order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        delivery_address=delivery_address if dining_option == 'Delivery' else None,
        dining_option=dining_option,
        table_number=table_number if dining_option == 'Dine-In' else None,
        special_instructions=special_instructions,
        payment_method="Cash", # Forced for MVP
        items_summary=", ".join(items_summary_list),
        items=raw_items,
        total_price=total_price,
        status="Pending",
        restaurant_id=g.restaurant.id
    )
    db.session.add(new_order)
    db.session.commit()
    
    # Clear the cart
    session.pop('cart', None)
    
    return render_template('checkout_success.html', restaurant=g.restaurant, order=new_order)

@app.route('/orders')
def orders():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    restaurant_orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).all()
    
    return render_template('order.html', orders=restaurant_orders)

@app.route('/orders/update/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    order = db.session.get(Order, order_id)
    if order and order.restaurant_id == restaurant.id:
        new_status = request.form.get('status')
        if new_status in ['Pending', 'Accepted', 'Delivered']:
            order.status = new_status
            db.session.commit()
            flash('Order status updated.')
            
    return redirect(url_for('orders'))

@app.route('/settings', methods=['GET'])
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    slides = HeroSlide.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template('settings.html', restaurant=restaurant, slides=slides)

@app.route('/settings/marquee', methods=['POST'])
def update_marquee():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    restaurant.marquee_text = request.form.get('marquee_text', '')
    db.session.commit()
    flash('Marquee text updated!')
    return redirect(url_for('settings'))

@app.route('/settings/slide/add', methods=['POST'])
def add_slide():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    image_url = request.form.get('image_url')
    heading = request.form.get('heading')
    subtext = request.form.get('subtext', '')
    
    if image_url and heading:
        new_slide = HeroSlide(
            image_url=image_url,
            heading=heading,
            subtext=subtext,
            restaurant_id=restaurant.id
        )
        db.session.add(new_slide)
        db.session.commit()
        flash('Slide added successfully!')
        
    return redirect(url_for('settings'))

@app.route('/settings/slide/delete/<int:slide_id>', methods=['POST'])
def delete_slide(slide_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    restaurant = Restaurant.query.filter_by(owner_id=user.id).first()
    
    slide = db.session.get(HeroSlide, slide_id)
    if slide and slide.restaurant_id == restaurant.id:
        db.session.delete(slide)
        db.session.commit()
        flash('Slide deleted.')
        
    return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))
