from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))

        new_user = User(username=username, full_name=full_name, email=email, password=password, role='user')
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/user')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        flash('Access denied')
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# Admin Dashboard View
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    lots = ParkingLot.query.all()
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin_dashboard.html', lots=lots, users=users)

# Create Lot
@app.route('/admin/create_lot', methods=['POST'])
@login_required
def create_lot():
    if not current_user.is_admin:
        abort(403)

    name = request.form['name']
    capacity = int(request.form['capacity'])
    price = float(request.form['price_per_hour'])

    lot = ParkingLot(name=name, capacity=capacity, price_per_hour=price)
    db.session.add(lot)
    db.session.commit()

    # Create spots
    for i in range(1, capacity + 1):
        spot = ParkingSpot(number=i, lot_id=lot.id)
        db.session.add(spot)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

# Delete Lot
@app.route('/admin/delete_lot/<int:lot_id>')
@login_required
def delete_lot(lot_id):
    if not current_user.is_admin:
        abort(403)

    lot = ParkingLot.query.get_or_404(lot_id)
    for spot in lot.spots:
        if spot.reservations:
            flash('Cannot delete lot with reservations.', 'danger')
            return redirect(url_for('admin_dashboard'))
        db.session.delete(spot)
    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# View Spots in Lot
@app.route('/admin/view_spots/<int:lot_id>')
@login_required
def view_spots(lot_id):
    if not current_user.is_admin:
        abort(403)

    lot = ParkingLot.query.get_or_404(lot_id)
    spots = lot.spots
    return render_template('view_spots.html', lot=lot, spots=spots)
