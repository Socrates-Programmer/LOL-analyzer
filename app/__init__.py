from flask import Flask
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    app.config["MONGODB_URI"] = os.environ.get("MONGODB_URI")
    
    # Crear cliente Mongo y obtener la BD por defecto
    client = MongoClient(app.config["MONGODB_URI"])
    app.db = client.get_default_database()
    
    from . import routes
    app.register_blueprint(routes.bp)
    
    return app
