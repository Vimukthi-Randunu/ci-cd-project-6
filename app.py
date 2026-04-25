import os
import time
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '5432')}"
    f"/{os.environ['DB_NAME']}"
)

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)

if os.environ.get('TESTING') != 'true':
    retries = 5
    while retries > 0:
        try:
            with app.app_context():
                db.create_all()
            break
        except Exception as e:
            retries -= 1
            print(f"Database not ready, retrying... ({retries} left)")
            time.sleep(3)
    if retries == 0:
        raise Exception("Could not connect to database after multiple retries")

@app.route('/')
def health():
    return jsonify({'status': 'ok'})

@app.route('/users')
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name, 'email': u.email} for u in users])