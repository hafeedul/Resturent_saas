from flask import current_app as app

@app.route('/')
def home():
    return "Hello, Portable SaaS! Running on Flask with Application Factory."
