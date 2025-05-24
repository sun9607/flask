from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

from util.appsettings import app

db = SQLAlchemy(app)


class Card(db.Model):
    __tablename__ = "card"

    count = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(45))
    order_id = db.Column(db.String(45))
    intro_type = db.Column(db.String(20), default="classic")
    intro_image = db.Column(db.String(500))
    video_file = db.Column(db.String(500))
    registerdate = db.Column(db.DateTime, default=func.now())


class Gallery(db.Model):
    __tablename__ = "gallery"

    id = db.Column(db.Integer, primary_key=True)
    card_no = db.Column(db.String(45))
    photo = db.Column(db.String(500))
