import os
from app import create_app, db
from app.models import User, Restaurant

app = create_app()

with app.app_context():
    db_path = os.path.join(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    
    # Create new tables
    db.create_all()
    print("Created new tables.")

    # Seed dummy user
    admin = User(name="Mario Rossi", email="mario@restaurant.com")
    admin.set_password("password123")
    db.session.add(admin)
    db.session.commit()
    print(f"Created user: {admin.email}")

    # Seed dummy restaurant linked to the user
    mario_pizza = Restaurant(
        name="Mario's Pizza",
        description="The best authentic Italian pizza in town. Established 1999.",
        domain="mario.127.0.0.1:5000",
        owner_id=admin.id
    )
    db.session.add(mario_pizza)
    db.session.commit()
    print(f"Created restaurant: {mario_pizza.name} on domain {mario_pizza.domain}")

    # Seed dummy menu items
    from app.models import MenuItem
    burger = MenuItem(
        name="Classic Burger",
        price=12.99,
        description="A delicious beef patty with lettuce, tomato, and cheese.",
        image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500&q=80",
        restaurant_id=mario_pizza.id
    )
    fries = MenuItem(
        name="Truffle Fries",
        price=6.99,
        description="Crispy fries tossed in truffle oil and parmesan.",
        image_url="https://images.unsplash.com/photo-1576107232684-1279f3908594?w=500&q=80",
        restaurant_id=mario_pizza.id
    )
    db.session.add_all([burger, fries])
    db.session.commit()
    print("Created dummy menu items.")

print("Database seeding complete!")
