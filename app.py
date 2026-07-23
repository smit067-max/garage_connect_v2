import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from bson import ObjectId

import models
import analytics
from ai_diagnosis import train_model, diagnose
from seed import seed_database

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
app.config['MONGO_URI'] = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/garage_connect')

mongo = PyMongo(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.username = user_doc['username']
        self.role = user_doc['role']
        self.full_name = user_doc.get('full_name', '')
        
@login_manager.user_loader
def load_user(user_id):
    user_doc = models.find_user_by_id(mongo.db, user_id)
    if user_doc:
        return User(user_doc)
    return None

# Role decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.before_request
def initialize():
    if not getattr(app, 'initialized', False):
        seed_database(mongo.db)
        app.initialized = True

# ----------------- PUBLIC ROUTES -----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_doc = models.find_user_by_username(mongo.db, username)
        
        if user_doc and models.verify_password(user_doc['password'], password):
            user = User(user_doc)
            login_user(user)
            flash("Logged in successfully.", "success")
            
            if user.role == 'customer':
                return redirect(url_for('garages'))
            elif user.role == 'garage_owner':
                return redirect(url_for('garage_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid username or password.", "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        if models.find_user_by_username(mongo.db, username):
            flash("Username already exists.", "error")
            return redirect(url_for('register'))
            
        models.create_user(mongo.db, username, email, password, role, full_name, phone)
        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))

# ----------------- CUSTOMER ROUTES -----------------
@app.route('/garages')
@login_required
@role_required('customer')
def garages():
    city = request.args.get('city')
    search = request.args.get('search')
    garage_list = models.find_all_garages(mongo.db, city=city, search=search)
    return render_template('garages.html', garages=garage_list)

@app.route('/garage/<id>')
@login_required
@role_required('customer')
def garage_detail(id):
    garage = models.find_garage_by_id(mongo.db, id)
    if not garage:
        flash("Garage not found.", "error")
        return redirect(url_for('garages'))
    reviews = models.get_reviews_for_garage(mongo.db, id)
    return render_template('garage_detail.html', garage=garage, reviews=reviews)

@app.route('/book/<garage_id>', methods=['GET', 'POST'])
@login_required
@role_required('customer')
def book_repair(garage_id):
    garage = models.find_garage_by_id(mongo.db, garage_id)
    if not garage:
        flash("Garage not found.", "error")
        return redirect(url_for('garages'))
        
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        vehicle_info = request.form.get('vehicle_info')
        problem_description = request.form.get('problem_description')
        scheduled_date = request.form.get('scheduled_date')
        
        ai_diag = diagnose(problem_description)
        models.create_booking(mongo.db, current_user.id, garage_id, service_type, vehicle_info, problem_description, ai_diag, scheduled_date)
        flash("Booking created successfully.", "success")
        return redirect(url_for('my_bookings'))
        
    return render_template('book_repair.html', garage=garage, services=garage.get('services', []))

@app.route('/my-bookings')
@login_required
@role_required('customer')
def my_bookings():
    bookings = models.find_bookings_by_customer(mongo.db, current_user.id)
    # Join garage info
    for b in bookings:
        b['garage'] = models.find_garage_by_id(mongo.db, b['garage_id'])
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/review/<booking_id>', methods=['POST'])
@login_required
@role_required('customer')
def submit_review(booking_id):
    booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
    if not booking or str(booking['customer_id']) != current_user.id:
        flash("Invalid booking.", "error")
        return redirect(url_for('my_bookings'))
        
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    models.create_review(mongo.db, booking_id, current_user.id, booking['garage_id'], rating, comment)
    flash("Review submitted.", "success")
    return redirect(url_for('my_bookings'))

# ----------------- GARAGE OWNER ROUTES -----------------
@app.route('/garage-dashboard')
@login_required
@role_required('garage_owner')
def garage_dashboard():
    garage = models.find_garage_by_owner(mongo.db, current_user.id)
    if not garage:
        return redirect(url_for('register_garage'))
        
    bookings = models.find_bookings_by_garage(mongo.db, garage['_id'])
    low_stock_items = models.get_low_stock_items(mongo.db, garage['_id'])
    stats = analytics.get_kpi_summary(mongo.db, garage['_id'], 'month')
    
    return render_template('garage_dashboard.html', garage=garage, bookings=bookings, low_stock_items=low_stock_items, stats=stats)

@app.route('/garage-analytics')
@login_required
@role_required('garage_owner')
def garage_analytics():
    garage = models.find_garage_by_owner(mongo.db, current_user.id)
    if not garage:
        return redirect(url_for('register_garage'))
    return render_template('garage_analytics.html', garage=garage)

@app.route('/booking/<id>/accept', methods=['POST'])
@login_required
@role_required('garage_owner')
def accept_booking(id):
    models.update_booking_status(mongo.db, id, "Accepted")
    flash("Booking accepted.", "success")
    return redirect(url_for('garage_dashboard'))

@app.route('/booking/<id>/start', methods=['POST'])
@login_required
@role_required('garage_owner')
def start_booking(id):
    models.update_booking_status(mongo.db, id, "In Progress")
    flash("Booking started.", "success")
    return redirect(url_for('garage_dashboard'))

@app.route('/booking/<id>/complete', methods=['GET', 'POST'])
@login_required
@role_required('garage_owner')
def complete_booking(id):
    booking = mongo.db.bookings.find_one({"_id": ObjectId(id)})
    garage = models.find_garage_by_owner(mongo.db, current_user.id)
    inventory_items = models.get_inventory(mongo.db, garage['_id'])
    
    if request.method == 'POST':
        labour_price = float(request.form.get('labour_price', 0))
        part_ids = request.form.getlist('part_id[]')
        quantities = request.form.getlist('quantity[]')
        
        parts_used = []
        for pid, qty in zip(part_ids, quantities):
            if pid and qty and int(qty) > 0:
                parts_used.append({"item_id": pid, "quantity": int(qty)})
                
        models.complete_booking(mongo.db, id, labour_price, parts_used)
        flash("Booking completed.", "success")
        return redirect(url_for('garage_dashboard'))
        
    return render_template('complete_booking.html', booking=booking, inventory_items=inventory_items)

@app.route('/register-garage', methods=['GET', 'POST'])
@login_required
@role_required('garage_owner')
def register_garage():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        city = request.form.get('city')
        phone = request.form.get('phone')
        services = request.form.getlist('services')
        operating_hours = request.form.get('operating_hours')
        
        models.create_garage(mongo.db, current_user.id, name, address, city, phone, services, operating_hours)
        flash("Garage registered and pending approval.", "success")
        return redirect(url_for('garage_dashboard'))
        
    return render_template('register_garage.html')

@app.route('/inventory')
@login_required
@role_required('garage_owner')
def inventory():
    garage = models.find_garage_by_owner(mongo.db, current_user.id)
    items = models.get_inventory(mongo.db, garage['_id'])
    return render_template('inventory.html', items=items, garage=garage)

@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
@role_required('garage_owner')
def add_part():
    garage = models.find_garage_by_owner(mongo.db, current_user.id)
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        quantity = int(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        low_stock_threshold = int(request.form.get('low_stock_threshold'))
        
        models.add_inventory_item(mongo.db, garage['_id'], name, category, quantity, unit_price, low_stock_threshold)
        flash("Item added.", "success")
        return redirect(url_for('inventory'))
        
    return render_template('add_part.html')

@app.route('/inventory/<id>/restock', methods=['POST'])
@login_required
@role_required('garage_owner')
def restock_part(id):
    quantity = int(request.form.get('quantity', 0))
    if quantity > 0:
        models.update_stock(mongo.db, id, quantity)
        flash("Stock updated.", "success")
    return redirect(url_for('inventory'))

@app.route('/inventory/<id>/delete', methods=['POST'])
@login_required
@role_required('garage_owner')
def delete_part(id):
    models.delete_inventory_item(mongo.db, id)
    flash("Item deleted.", "success")
    return redirect(url_for('inventory'))

# ----------------- ADMIN ROUTES -----------------
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    pending_garages = list(mongo.db.garages.find({"is_approved": False}))
    approved_garages = list(mongo.db.garages.find({"is_approved": True}))
    recent_bookings = list(mongo.db.bookings.find().sort("created_at", -1).limit(10))
    low_stock_all = models.get_low_stock_items(mongo.db)
    
    pipeline = [{"$match": {"status": "Completed"}}, {"$group": {"_id": None, "total": {"$sum": "$commission_amount"}}}]
    total_comm_res = list(mongo.db.bookings.aggregate(pipeline))
    total_commission = total_comm_res[0]['total'] if total_comm_res else 0
    
    monthly_commission = total_commission * 0.2
    
    return render_template('admin_dashboard.html', 
                           pending_garages=pending_garages, 
                           approved_garages=approved_garages,
                           total_commission=total_commission,
                           monthly_commission=monthly_commission,
                           low_stock_all=low_stock_all,
                           recent_bookings=recent_bookings)

@app.route('/admin/approve/<garage_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_garage(garage_id):
    models.approve_garage(mongo.db, garage_id)
    flash("Garage approved.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<garage_id>', methods=['POST'])
@login_required
@role_required('admin')
def reject_garage(garage_id):
    models.reject_garage(mongo.db, garage_id)
    flash("Garage rejected.", "success")
    return redirect(url_for('admin_dashboard'))

# ----------------- API ROUTES -----------------
@app.route('/api/diagnose', methods=['POST'])
@csrf.exempt
def api_diagnose():
    data = request.get_json()
    text = data.get('text', '')
    result = diagnose(text)
    return jsonify(result)

@app.route('/api/garage/analytics')
@login_required
@role_required('garage_owner')
def api_analytics():
    period = request.args.get('period', 'month')
    garage = models.find_garage_by_owner(mongo.db, current_user.id)
    g_id = garage['_id']
    
    return jsonify({
        "kpi": analytics.get_kpi_summary(mongo.db, g_id, period),
        "revenue_trend": analytics.get_revenue_trend(mongo.db, g_id, period),
        "service_breakdown": analytics.get_service_breakdown(mongo.db, g_id, period),
        "customer_stats": analytics.get_customer_stats(mongo.db, g_id, period),
        "parts_usage": analytics.get_parts_usage(mongo.db, g_id, period),
        "peak_days": analytics.get_peak_days(mongo.db, g_id, period)
    })

if __name__ == '__main__':
    train_model()
    app.run(debug=True, port=5000)
