
from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from extensions import db, migrate
from routes import bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv('SECRET_KEY')

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    app.register_blueprint(bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
