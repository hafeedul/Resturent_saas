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
    user = User(name="Owner", email="owner@cheezytown.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    print(f"Created user: {user.email}")

    # Seed dummy restaurant
    from app.models import Restaurant
    cheezy_town = Restaurant(
        name="Cheezy Town", 
        description="The cheesiest, most mouth-watering burgers in town!", 
        domain="cheezy.127.0.0.1:5000", 
        owner_id=user.id
    )
    db.session.add(cheezy_town)
    db.session.commit()
    print(f"Created restaurant: {cheezy_town.name} on domain {cheezy_town.domain}")

    # Seed dummy menu items
    from app.models import MenuItem
    burger = MenuItem(
        name="The Cheezy Monster",
        price=12.99,
        description="Triple beef patty, quadruple cheddar cheese, special house sauce, crispy onions, all hugged by a brioche bun.",
        image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=600&auto=format&fit=crop",
        restaurant_id=cheezy_town.id
    )
    fries = MenuItem(
        name="Loaded Cheezy Fries",
        price=6.99,
        description="Crispy golden fries smothered in our signature liquid gold cheese and topped with smoked bacon bits.",
        image_url="https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?q=80&w=600&auto=format&fit=crop",
        restaurant_id=cheezy_town.id
    )
    shake = MenuItem(
        name="Chocolate Lava Shake",
        price=5.99,
        description="Thick chocolate milkshake with brownie chunks and whipped cream.",
        image_url="https://images.unsplash.com/photo-1572490122747-3968b75cc699?q=80&w=600&auto=format&fit=crop",
        restaurant_id=cheezy_town.id
    )
    
    db.session.add(burger)
    db.session.add(fries)
    db.session.add(shake)
    db.session.commit()
    print("Created dummy menu items.")

print("Database seeding complete!")
