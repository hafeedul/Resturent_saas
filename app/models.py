from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # We will expand this model later (password hashes, stripe_customer_id, etc.)

    def __repr__(self):
        return f'<User {self.email}>'
