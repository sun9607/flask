import os

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "../uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('SQL_USER')}:{os.getenv('SQL_PASSWORD')}@localhost/invitationcard_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
