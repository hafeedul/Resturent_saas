from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # A user can manage one or more restaurants
    restaurants = db.relationship('Restaurant', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    marquee_text = db.Column(db.Text, default="🔥 100% PREMIUM BEEF 🔥 FRESHLY BAKED BUNS 🔥 MELTED CHEEZE 🔥 ICE COLD SHAKES 🔥 CRAZY DEALS 🔥")
    domain = db.Column(db.String(100), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='restaurant', lazy=True)
    # One-to-many relationship with hero slides
    hero_slides = db.relationship('HeroSlide', backref='restaurant', lazy=True, cascade="all, delete-orphan")

class HeroSlide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500), nullable=False)
    heading = db.Column(db.String(200), nullable=False)
    subtext = db.Column(db.Text)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(50), default="Main")
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    delivery_address = db.Column(db.Text, nullable=True)
    
    dining_option = db.Column(db.String(50), nullable=False, default="Delivery")
    table_number = db.Column(db.String(20), nullable=True)
    special_instructions = db.Column(db.Text, nullable=True)
    
    items = db.Column(db.JSON, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False, default="Cash")
    items_summary = db.Column(db.Text, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Order {self.id}>'
