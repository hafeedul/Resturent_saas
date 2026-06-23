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
    admin = User(email="mario@restaurant.com")
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

print("Database seeding complete!")
