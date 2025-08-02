from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# -------------------- Constants -------------------- #
SPOT_STATUS_AVAILABLE = "AVAILABLE"
SPOT_STATUS_OCCUPIED = "OCCUPIED"

USER_ROLE_USER = "user"
USER_ROLE_ADMIN = "admin"

# -------------------- Models -------------------- #

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False, default=USER_ROLE_USER)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    reservations = db.relationship("Reservation", backref="user", cascade="all, delete-orphan")

    def is_admin(self):
        return self.role == USER_ROLE_ADMIN

class ParkingLot(db.Model):
    __tablename__ = "parking_lots"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(6), nullable=False, index=True)
    total_spots = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    spots = db.relationship("ParkingSpot", backref="lot", cascade="all, delete-orphan")

class ParkingSpot(db.Model):
    __tablename__ = "parking_spots"

    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), default=SPOT_STATUS_AVAILABLE)
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lots.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reservation = db.relationship("Reservation", backref="spot", cascade="all, delete-orphan", uselist=False)

class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spots.id"), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    total_time = db.Column(db.Integer, nullable=True)  # in minutes
    cost = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    