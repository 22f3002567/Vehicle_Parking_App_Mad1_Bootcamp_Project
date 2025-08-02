from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms import StringField, IntegerField, FloatField, SubmitField, PasswordField, SelectField, HiddenField, BooleanField

from wtforms.validators import DataRequired, Email, EqualTo, Length
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

# --- App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Import Models ---
from models import db, User, ParkingLot, ParkingSpot, Reservation

# --- Extensions ---
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# --- User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Flask-WTF Forms ---
# class RegisterForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
#     full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
#     confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
#     submit = SubmitField('Register')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired()])  # removed Email() validator
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddLotForm(FlaskForm):
    name = StringField('Lot Name', validators=[DataRequired(), Length(max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    address = StringField('Address', validators=[DataRequired(), Length(max=300)])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=5, max=6)])
    total_spots = IntegerField('Total Spots', validators=[DataRequired() ])
    price = FloatField('Price per Hour (₹)', validators=[DataRequired()])
    submit = SubmitField('Add Lot')

class SpotForm(FlaskForm):
    spot_number = StringField("Spot Number", validators=[DataRequired()])
    status = SelectField('Status', choices=[('AVAILABLE', 'Available'), ('OCCUPIED', 'Occupied')])
    lot_id = HiddenField()
    is_available = BooleanField('Available')
    submit = SubmitField("Add Spot")
    


# --- Setup DB and Initial Admin ---
def setup_initial_admin():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='Siddharth').first():
            admin = User(
                username='Siddharth',
                full_name='Siddharth Sahu',
                email='Siddharth@admin.com',
                password=generate_password_hash('sidd@123', method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()

setup_initial_admin()

# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first():
            flash('Username or email already exists.', 'warning')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(
            username=form.username.data,
            full_name=form.full_name.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    lots = ParkingLot.query.all()
    reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.start_time.desc()).all()
    return render_template('user_dashboard.html', lots=lots, reservations=reservations)

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    lots = ParkingLot.query.all()
    users = User.query.all()
    spots = ParkingSpot.query.all()
    bookings = Reservation.query.order_by(Reservation.start_time.desc()).all()

    active_bookings = Reservation.query.filter(Reservation.end_time == None).count()

    total_revenue = sum(res.cost or 0 for res in bookings if res.cost) 

    # Earnings Chart
    # earnings = {}
    # for lot in lots:
    #     total = 0
    #     for spot in lot.spots:
    #         if spot.reservation and spot.reservation.cost:
    #             total += spot.reservation.cost
    #     earnings[lot.name] = total

    earnings = {}
    for lot in lots:
        lot_reservations = [r for r in bookings if r.spot.lot_id == lot.id and r.cost]
        earnings[lot.name] = sum(r.cost for r in lot_reservations)


    fig, ax = plt.subplots()
    ax.bar(earnings.keys(), earnings.values(), color='skyblue')
    ax.set_title('Earnings per Lot')
    ax.set_ylabel('Earnings (₹)')
    plt.xticks(rotation=45)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    # return render_template('admin_dashboard.html', lots=lots, users=users, chart_data=chart_data)
    return render_template(
        'admin_dashboard.html',
        lots=lots,
        users=users,
        bookings=bookings, 
        spots=spots,        
        total_users=len(users), 
        total_lots=len(lots),
        total_revenue=total_revenue,
        active_bookings=active_bookings,
        chart_data=chart_data
    )

# --- Routes of manage_lots ---
@app.route('/admin/manage_lots', methods=['GET'])
@login_required
def manage_lots():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))
    lots = ParkingLot.query.all()
    return render_template('manage_lots.html', lots=lots)

@app.route('/admin/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def edit_lot(lot_id):
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))
    lot = ParkingLot.query.get_or_404(lot_id)
    form = AddLotForm(obj=lot)
    if form.validate_on_submit():
        lot.name = form.name.data
        lot.location = form.location.data
        #lot.address = form.address.data
        lot.pincode = form.pincode.data
        lot.price_per_hour = form.price.data
        lot.total_spots = form.total_spots.data
        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('manage_lots'))
    return render_template('edit_lot.html', form=form, lot=lot)


@app.route('/admin/delete_lot/<int:lot_id>', methods=['POST'])
@login_required
def delete_lot(lot_id):
    if current_user.role != 'admin':
        abort(403)

    lot = ParkingLot.query.get_or_404(lot_id)

    # Check if any spot is not AVAILABLE
    if any(spot.status != 'AVAILABLE' for spot in lot.spots):
        flash('Cannot delete this lot. Some spots are currently reserved or in use.', 'warning')
        return redirect(url_for('manage_lots'))

    try:
        # Safe to delete since all spots are AVAILABLE
        for spot in lot.spots:
            db.session.delete(spot)

        db.session.delete(lot)
        db.session.commit()
        flash('Parking lot deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the lot.', 'danger')

    return redirect(url_for('manage_lots'))
@app.route('/admin/add_lot', methods=['GET', 'POST'])
@login_required
def add_lot():
    if current_user.role != 'admin':
        abort(403)

    form = AddLotForm()
    if form.validate_on_submit():
        # Step 1: Create and stage the new lot
        lot = ParkingLot(
            name=form.name.data,
            location=form.location.data,
            address=form.address.data,
            pincode=form.pincode.data,
            price_per_hour=form.price.data,
            total_spots=form.total_spots.data
        )
        db.session.add(lot)
        db.session.flush()  # Get lot.id before commit

        # Step 2: Generate all spots
        total_spots = int(form.total_spots.data)
        lot_prefix = lot.name[:3].upper()

        for i in range(1, total_spots + 1):
            spot = ParkingSpot(
                spot_number=f"{lot_prefix}-{i}",
                status='AVAILABLE',
                lot_id=lot.id
            )
            db.session.add(spot)

        # Step 3: Commit all at once
        db.session.commit()

        flash('Parking lot and spots added successfully.', 'success')
        return redirect(url_for('manage_lots'))

    return render_template('add_lot.html', form=form)

# @app.route('/admin/add_spot/<int:lot_id>', methods=['GET', 'POST'])
# @login_required
# def add_spot(lot_id):
#     if current_user.role != 'admin':
#         abort(403)

#     lot = ParkingLot.query.get_or_404(lot_id)
#     form = SpotForm()

#     if form.validate_on_submit():
#         new_spot = ParkingSpot(
#             lot_id=lot.id,
#             spot_number=form.spot_number.data,
#             status='AVAILABLE'  # defaulting to available
#         )
#         db.session.add(new_spot)
#     db.session.commit()
#     flash(f"Spot '{new_spot.spot_number}' added to {lot.name}.", 'success')
#     return redirect(url_for('manage_lots'))  # or 'admin_dashboard' if you prefer

#     return render_template('add_spot.html', form=form, lot=lot)

@app.route('/admin/add_spot/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def add_spot(lot_id):
    if current_user.role != 'admin':
        abort(403)

    lot = ParkingLot.query.get_or_404(lot_id)
    form = SpotForm()

    if form.validate_on_submit():
        new_spot = ParkingSpot(
            lot_id=lot.id,
            spot_number=form.spot_number.data,
            status='AVAILABLE'
        )
        db.session.add(new_spot)
        db.session.commit() 

        flash(f"Spot '{new_spot.spot_number}' added to {lot.name}.", 'success')
        return redirect(url_for('manage_spots', lot_id=lot.id))  

    return render_template('add_spot.html', form=form, lot=lot) 


@app.route('/admin/manage_spots/<int:lot_id>')
@login_required
def manage_spots(lot_id):
    if current_user.role != 'admin':
        abort(403)

    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()

    available = len([s for s in spots if s.status == 'AVAILABLE'])
    occupied = len([s for s in spots if s.status == 'OCCUPIED'])

    return render_template('manage_spots.html', lot=lot, spots=spots, available=available, occupied=occupied)

@app.route('/admin/edit_spot/<int:spot_id>', methods=['GET', 'POST'])
@login_required
def edit_spot(spot_id):
    if current_user.role != 'admin':
        abort(403)

    spot = ParkingSpot.query.get_or_404(spot_id)
    form = SpotForm(obj=spot)

    if request.method == 'GET':
        form.lot_id.data = str(spot.lot_id)

    if form.validate_on_submit():
        spot.spot_number = form.spot_number.data
        db.session.commit()
        flash(f"Spot '{spot.spot_number}' updated successfully.", 'success')
        return redirect(url_for('manage_spots', lot_id=spot.lot_id))

    return render_template('edit_spot.html', form=form, spot=spot)

@app.route('/admin/delete_spot/<int:spot_id>', methods=['POST'])
@login_required
def delete_spot(spot_id):
    if current_user.role != 'admin':
        abort(403)

    spot = ParkingSpot.query.get_or_404(spot_id)
    lot_id = spot.lot_id

    if spot.status != 'AVAILABLE':
        flash('Cannot delete this spot. It is currently occupied.', 'warning')
        return redirect(url_for('manage_spots', lot_id=lot_id))

    db.session.delete(spot)
    db.session.commit()
    flash('Spot deleted successfully.', 'success')
    return redirect(url_for('manage_spots', lot_id=lot_id))


@app.route('/lot/<int:lot_id>')
@login_required
def view_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    return render_template('lot_view.html', lot=lot)

@app.route('/reserve/<int:lot_id>/<int:spot_id>', methods=['POST'])
@login_required
def reserve_spot(lot_id, spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status == 'OCCUPIED':
        flash('Spot is already reserved.', 'warning')
        return redirect(url_for('view_lot', lot_id=lot_id))

    spot.status = 'OCCUPIED'
    reservation = Reservation(
        user_id=current_user.id,
        spot_id=spot.id,
        vehicle_number=request.form['vehicle_number'],
        start_time=datetime.utcnow()
    )
    db.session.add(reservation)
    db.session.commit()
    flash('Spot reserved successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/checkout/<int:reservation_id>', methods=['POST'])
@login_required
def checkout(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard'))

    reservation.end_time = datetime.utcnow()
    duration = (reservation.end_time - reservation.start_time).total_seconds() / 60
    rate = reservation.spot.lot.price_per_hour or 10
    reservation.total_time = int(duration)
    reservation.cost = round((duration / 60) * rate, 2)
    reservation.spot.status = 'AVAILABLE'
    db.session.commit()
    flash(f'Checked out. Total cost: ₹{reservation.cost}', 'success')
    return redirect(url_for('dashboard'))

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
