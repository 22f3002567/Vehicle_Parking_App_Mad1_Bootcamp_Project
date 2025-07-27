from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default="user")

    reservations = db.relationship("Reservation", backref="user", cascade="all, delete-orphan")

class ParkingLot(db.Model):
    __tablename__ = "parking_lots"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    total_spots = db.Column(db.Integer, nullable=False)

    spots = db.relationship("ParkingSpot", backref="lot", cascade="all, delete-orphan")

class ParkingSpot(db.Model):
    __tablename__ = "parking_spots"

    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="EMPTY") 
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lots.id"), nullable=False)

    reservation = db.relationship("Reservation", backref="spot", cascade="all, delete-orphan")

class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spots.id"), nullable=False)

    start_time = db.Column(db.DateTime, server_default=db.func.now())
    end_time = db.Column(db.DateTime, nullable=True)
    total_time = db.Column(db.Integer, nullable=True) 
    cost = db.Column(db.Float, nullable=True)
