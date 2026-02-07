#!/usr/bin/env python3
"""
NAVIGo - Intelligent Tourism System
Flask Backend Application
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import requests
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database connection
# - Default: local SQLite
# - Production: set DATABASE_URL (Postgres or SQLite on persistent disk)
_database_url = os.getenv('DATABASE_URL', '').strip()
if _database_url:
    # Some providers still provide postgres:// URLs; SQLAlchemy expects postgresql://
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = _database_url
else:
    # Relative SQLite file (local dev). Override with SQLITE_DATABASE_URI if needed.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLITE_DATABASE_URI', 'sqlite:///navigo.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# API Keys
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_KEY', '')


# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    preferences = db.Column(db.Text)  # JSON string for user preferences
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    travel_plans = db.relationship('TravelPlan', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')


class Destination(db.Model):
    __tablename__ = 'destinations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    state = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    rating = db.Column(db.Float, default=0.0)
    popularity = db.Column(db.Integer, default=0)
    best_time = db.Column(db.String(200))
    ideal_weather = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Relationships
    bookings = db.relationship('Booking', backref='destination', lazy=True)
    reviews = db.relationship('Review', backref='destination', lazy=True, cascade='all, delete-orphan')


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.id'), nullable=True)
    
    # Booking details (stored as JSON for flexibility)
    services = db.Column(db.Text)  # JSON array of selected services
    options = db.Column(db.Text)   # JSON object of selected options
    traveler_name = db.Column(db.String(200))
    traveler_email = db.Column(db.String(200))
    traveler_phone = db.Column(db.String(20))
    num_travelers = db.Column(db.Integer, default=1)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    special_requirements = db.Column(db.Text)
    
    # Financial
    amount = db.Column(db.Float, nullable=False)
    gst = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled
    payment_method = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TravelPlan(db.Model):
    __tablename__ = 'travel_plans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destination_ids = db.Column(db.Text)  # JSON array of destination IDs
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    route_data = db.Column(db.Text)  # JSON route information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Helper Functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def get_weather_data(lat, lon):
    """Fetch weather data from OpenWeather API"""
    if not OPENWEATHER_API_KEY:
        return None
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Weather API error: {e}")
    return None


# Routes - Pages
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/manifest.webmanifest')
def manifest():
    resp = make_response(send_from_directory('static', 'manifest.webmanifest'))
    resp.headers['Content-Type'] = 'application/manifest+json; charset=utf-8'
    return resp

@app.route('/sw.js')
def service_worker():
    # Service worker must be served from site root for full scope
    resp = make_response(send_from_directory('static', 'sw.js'))
    resp.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    # Allow updates without aggressive caching
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html', google_maps_key=GOOGLE_MAPS_KEY)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/plan')
@login_required
def plan():
    return render_template('plan.html')


@app.route('/booking')
@login_required
def booking():
    return render_template('booking.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))


# Routes - Authentication API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {'id': user.id, 'username': user.username, 'email': user.email}
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 400
    
    # Create new user
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Account created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error creating account'}), 500


# Routes - Destinations API
@app.route('/api/destinations')
def get_destinations():
    """Get all destinations with optional filters"""
    category = request.args.get('category', 'all')
    state = request.args.get('state', 'all')
    sort = request.args.get('sort', 'popularity')
    search = request.args.get('search', '').strip()
    
    query = Destination.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    if state != 'all':
        query = query.filter_by(state=state)
    if search:
        query = query.filter(Destination.name.contains(search))
    
    # Sorting
    if sort == 'rating':
        query = query.order_by(Destination.rating.desc())
    elif sort == 'name':
        query = query.order_by(Destination.name)
    else:  # popularity (default)
        query = query.order_by(Destination.popularity.desc())
    
    destinations = query.all()
    
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'category': d.category,
        'state': d.state,
        'latitude': d.latitude,
        'longitude': d.longitude,
        'image_url': d.image_url,
        'rating': d.rating,
        'popularity': d.popularity,
        'best_time': d.best_time,
        'ideal_weather': d.ideal_weather,
        'description': d.description
    } for d in destinations])


@app.route('/api/destination/<int:dest_id>')
def get_destination(dest_id):
    """Get destination details"""
    dest = Destination.query.get_or_404(dest_id)
    
    # Get reviews
    reviews = Review.query.filter_by(destination_id=dest_id).order_by(Review.created_at.desc()).limit(10).all()
    
    return jsonify({
        'id': dest.id,
        'name': dest.name,
        'category': dest.category,
        'state': dest.state,
        'latitude': dest.latitude,
        'longitude': dest.longitude,
        'image_url': dest.image_url,
        'rating': dest.rating,
        'popularity': dest.popularity,
        'best_time': dest.best_time,
        'ideal_weather': dest.ideal_weather,
        'description': dest.description,
        'reviews': [{
            'id': r.id,
            'user': r.user.username,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat()
        } for r in reviews]
    })


@app.route('/api/weather/<int:dest_id>')
def get_weather(dest_id):
    """Get weather for a destination"""
    dest = Destination.query.get_or_404(dest_id)
    
    if not dest.latitude or not dest.longitude:
        return jsonify({'error': 'Destination coordinates not available'}), 404
    
    weather_data = get_weather_data(dest.latitude, dest.longitude)
    
    if not weather_data:
        return jsonify({
            'available': False,
            'message': 'Weather data not available'
        })
    
    temp = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']
    description = weather_data['weather'][0]['description']
    icon = weather_data['weather'][0]['icon']
    
    # Determine suitability
    suitable = True
    if dest.ideal_weather:
        ideal_temp_range = dest.ideal_weather.split('-')
        if len(ideal_temp_range) == 2:
            try:
                min_temp = float(ideal_temp_range[0])
                max_temp = float(ideal_temp_range[1])
                suitable = min_temp <= temp <= max_temp
            except:
                pass
    
    return jsonify({
        'available': True,
        'temperature': temp,
        'humidity': humidity,
        'description': description,
        'icon': icon,
        'suitable': suitable,
        'raw': weather_data
    })


# Routes - Booking API
@app.route('/api/bookings', methods=['POST'])
@login_required
def create_booking():
    """Create a new booking"""
    data = request.get_json()
    user_id = session['user_id']
    
    try:
        # Calculate amounts
        services = data.get('services', [])
        options = data.get('options', {})
        num_travelers = int(data.get('travelers', 1))
        
        # Calculate base amount
        base_amount = 0.0
        for service_type, option_data in options.items():
            if isinstance(option_data, dict) and 'price' in option_data:
                base_amount += option_data['price'] * num_travelers
        
        # Calculate GST (18%)
        gst = base_amount * 0.18
        total_amount = base_amount + gst
        
        # Parse dates
        start_date = None
        end_date = None
        if data.get('startDate'):
            start_date = datetime.strptime(data.get('startDate'), '%Y-%m-%d').date()
        if data.get('endDate'):
            end_date = datetime.strptime(data.get('endDate'), '%Y-%m-%d').date()
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            services=json.dumps(services),
            options=json.dumps(options),
            traveler_name=data.get('traveler', {}).get('name', ''),
            traveler_email=data.get('traveler', {}).get('email', ''),
            traveler_phone=data.get('traveler', {}).get('phone', ''),
            num_travelers=num_travelers,
            start_date=start_date,
            end_date=end_date,
            special_requirements=data.get('specialRequirements', ''),
            amount=base_amount,
            gst=gst,
            total_amount=total_amount,
            status='confirmed',
            payment_method=data.get('paymentMethod', 'card')
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'booking_id': booking.id,
            'message': 'Booking created successfully',
            'booking': {
                'id': booking.id,
                'total_amount': booking.total_amount,
                'status': booking.status,
                'created_at': booking.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Booking error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error creating booking: {str(e)}'
        }), 500


@app.route('/api/bookings/my')
@login_required
def get_my_bookings():
    """Get current user's bookings"""
    user_id = session['user_id']
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    
    return jsonify([{
        'id': b.id,
        'services': json.loads(b.services) if b.services else [],
        'options': json.loads(b.options) if b.options else {},
        'traveler_name': b.traveler_name,
        'traveler_email': b.traveler_email,
        'traveler_phone': b.traveler_phone,
        'num_travelers': b.num_travelers,
        'start_date': b.start_date.isoformat() if b.start_date else None,
        'end_date': b.end_date.isoformat() if b.end_date else None,
        'amount': b.amount,
        'gst': b.gst,
        'total_amount': b.total_amount,
        'status': b.status,
        'payment_method': b.payment_method,
        'created_at': b.created_at.isoformat()
    } for b in bookings])


# Routes - Travel Plan API
@app.route('/api/plan/save', methods=['POST'])
@login_required
def save_plan():
    """Save a travel plan"""
    data = request.get_json()
    user_id = session['user_id']
    
    try:
        plan = TravelPlan(
            user_id=user_id,
            destination_ids=json.dumps(data.get('destinations', [])),
            start_date=datetime.strptime(data.get('startDate'), '%Y-%m-%d').date() if data.get('startDate') else None,
            end_date=datetime.strptime(data.get('endDate'), '%Y-%m-%d').date() if data.get('endDate') else None,
            route_data=json.dumps(data.get('route', {}))
        )
        
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'plan_id': plan.id,
            'message': 'Travel plan saved successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error saving plan: {str(e)}'
        }), 500


# Routes - Chatbot API
@app.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot():
    """AI Chatbot endpoint using Gemini"""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    if not GEMINI_API_KEY:
        # Fallback response if API key not configured
        return jsonify({
            'response': 'I\'m sorry, the AI chatbot is not configured. Please set GEMINI_API_KEY in your environment variables.'
        })
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""You are a helpful travel assistant for NAVIGo, an Indian tourism platform. 
        Answer the following question about travel in India: {message}
        
        Provide a concise, helpful response."""
        
        response = model.generate_content(prompt)
        return jsonify({'response': response.text})
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            'response': 'I apologize, but I\'m having trouble processing your request right now. Please try again later.'
        })


# Routes - Reviews API
@app.route('/api/reviews/<int:dest_id>')
def get_reviews(dest_id):
    """Get reviews for a destination"""
    reviews = Review.query.filter_by(destination_id=dest_id).order_by(Review.created_at.desc()).all()
    
    return jsonify([{
        'id': r.id,
        'user': r.user.username,
        'rating': r.rating,
        'comment': r.comment,
        'created_at': r.created_at.isoformat()
    } for r in reviews])


@app.route('/api/reviews', methods=['POST'])
@login_required
def create_review():
    """Create a review"""
    data = request.get_json()
    user_id = session['user_id']
    destination_id = data.get('destination_id')
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if not destination_id or not rating:
        return jsonify({'success': False, 'message': 'Destination ID and rating are required'}), 400
    
    if rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
    
    try:
        review = Review(
            user_id=user_id,
            destination_id=destination_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(review)
        
        # Update destination rating
        dest = Destination.query.get(destination_id)
        if dest:
            all_reviews = Review.query.filter_by(destination_id=destination_id).all()
            avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
            dest.rating = round(avg_rating, 2)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'review_id': review.id,
            'message': 'Review added successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating review: {str(e)}'
        }), 500


# Initialize Database
def init_db():
    """Initialize database with sample data if needed"""
    with app.app_context():
        db.create_all()
        
        # Check if destinations already exist
        if Destination.query.count() == 0:
            print("Initializing database with sample destinations...")
            # Add some sample destinations
            sample_destinations = [
                Destination(
                    name="Taj Mahal",
                    category="Heritage",
                    state="Uttar Pradesh",
                    latitude=27.1751,
                    longitude=78.0421,
                    image_url="https://images.unsplash.com/photo-1564507592333-c60657eea523",
                    rating=4.8,
                    popularity=100,
                    best_time="October to March",
                    ideal_weather="15-30",
                    description="Iconic white marble mausoleum, one of the Seven Wonders of the World"
                ),
                Destination(
                    name="Goa Beaches",
                    category="Beach",
                    state="Goa",
                    latitude=15.2993,
                    longitude=74.1240,
                    image_url="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2",
                    rating=4.6,
                    popularity=95,
                    best_time="November to February",
                    ideal_weather="20-30",
                    description="Beautiful beaches, vibrant nightlife, and Portuguese heritage"
                ),
                # Add more destinations as needed
            ]
            
            for dest in sample_destinations:
                db.session.add(dest)
            
            db.session.commit()
            print(f"Added {len(sample_destinations)} sample destinations")


# Ensure tables exist when running under gunicorn (module import)
if os.getenv('INIT_DB_ON_STARTUP', '1') == '1':
    try:
        init_db()
    except Exception as e:
        # Don't crash deploy if DB is temporarily unavailable (e.g., first boot)
        print(f"DB init skipped/failed: {e}")


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host='0.0.0.0', port=port)


