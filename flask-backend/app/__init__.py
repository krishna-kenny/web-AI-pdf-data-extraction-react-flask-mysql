from flask import Flask
from app.routes import main  # import your blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(main)
    return app
