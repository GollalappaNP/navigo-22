from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime, timedelta
import os
from functools import wraps
from urllib.parse import quote_plus
import importlib

genai = None
try:  # pragma: no cover
    genai = importlib.import_module("google.generativeai")
except ImportError:
    pass

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///navigo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# API Keys - GET YOUR FREE KEYS FROM:
# OpenWeather: https://openweathermap.org/api
# Google Maps: https://console.cloud.google.com/
OPENWEATHER_API_KEY = '4a4bde16be3efdba9b43ae3c348b19ae'
GOOGLE_MAPS_API_KEY = 'AIzaSyAMelgOa_8fKzAzrhlpxkKvBglllY7UTII'
DEFAULT_GEMINI_API_KEY = "AIzaSyB5IFsy_o7J5_RAyPu9bl4JaIjypzHduUI"
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', DEFAULT_GEMINI_API_KEY)
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash')
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
UNSPLASH_FALLBACK_BASE = "https://source.unsplash.com/featured/?"
OLD_IMAGE_HOSTS = ("images.unsplash.com", "source.unsplash.com")

if GEMINI_API_KEY and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_MODEL = genai.GenerativeModel(GEMINI_MODEL_NAME)
    except Exception as exc:
        GEMINI_MODEL = None
        print(f"⚠️  Gemini configuration failed: {exc}")
else:
    GEMINI_MODEL = None
    if not GEMINI_API_KEY:
        print("⚠️  GEMINI_API_KEY not found. Chatbot will use FAQ responses only.")
    elif not genai:
        print("⚠️  google-generativeai is missing. Install it and restart to enable Gemini.")

TOURISM_FAQS = [
    {
        "question": "What is the best time to visit major regions in India?",
        "answer": "North & Central India (Delhi, Rajasthan, Uttar Pradesh): October to March for cool weather.\nSouth India & Kerala: November to February for pleasant temperatures.\nHimalayas & Ladakh: May to September once mountain passes open.\nGoa & Beaches: November to February for dry, sunny days.",
        "keywords": ["best time", "when to visit", "season", "weather", "month"]
    },
    {
        "question": "How much does an India trip cost?",
        "answer": "Approximate daily budgets per person:\n• Backpacking: ₹1,500-2,500 (hostels, public transport, street food)\n• Mid-range: ₹3,500-7,000 (3-star hotels, mix of restaurants & cabs)\n• Premium: ₹10,000+ (resorts, flights between cities, guided tours)\nMetro cities and hill stations cost slightly more.",
        "keywords": ["budget", "cost", "price", "expense", "cheap"]
    },
    {
        "question": "What visa do foreign tourists need for India?",
        "answer": "Most travelers use the e-Tourist Visa from https://indianvisaonline.gov.in. Apply at least 4 days before travel, upload passport + photo, and carry a printed copy. Valid for 30 days, 1 year, or 5 years depending on nationality. Passport must be valid for 6+ months.",
        "keywords": ["visa", "e-visa", "documents", "entry"]
    },
    {
        "question": "Is India safe for travelers?",
        "answer": "India is generally safe if you follow standard travel precautions: avoid isolated areas late night, use registered taxis or ride-sharing apps, keep valuables secured, drink bottled water, and respect local customs. Women should dress modestly at religious sites and consider apps like Safetipin for safety ratings.",
        "keywords": ["safety", "safe", "crime", "secure"]
    },
    {
        "question": "How do I travel between Indian cities?",
        "answer": "Use flights for long distances (Air India, Indigo, Vistara), trains for scenic affordable journeys (book via IRCTC), and Volvo/state buses for hill stations. Within cities use metros, Uber/Ola, prepaid taxis, or auto-rickshaws (insist on meter).",
        "keywords": ["transport", "train", "bus", "flight", "cab"]
    },
    {
        "question": "What should I pack for an India trip?",
        "answer": "Pack light cotton outfits for plains, layers for mountains, comfortable walking shoes, sunscreen, hat, sunglasses, universal adapter (Type C/D/M), basic medicines, and modest clothing for temples. Monsoon travelers should add rain jackets and quick-dry footwear.",
        "keywords": ["pack", "packing", "clothes", "what to bring"]
    },
    {
        "question": "What are must-try Indian foods?",
        "answer": "North: butter chicken, chole bhature, kebabs. South: masala dosa, idli, filter coffee. West: pav bhaji, vada pav, Gujarati thali. East: rosogolla, fish curry. Always ask for spice level, start with bottled water, and try famous street food markets like Chandni Chowk or Mohammad Ali Road with hygiene in mind.",
        "keywords": ["food", "cuisine", "eat", "restaurant", "street food"]
    },
    {
        "question": "How does the Indian currency work?",
        "answer": "Currency is the Indian Rupee (₹ / INR). ATMs are common in cities, UPI/QR code payments work almost everywhere, and credit cards are accepted in hotels/malls. Carry some cash for markets or remote areas. Exchange money at banks/authorized counters, avoid street touts.",
        "keywords": ["currency", "money", "rupee", "atm", "exchange"]
    },
    {
        "question": "Which festivals should tourists experience?",
        "answer": "Top cultural festivals: Diwali (Oct/Nov lights), Holi (Mar colors, Mathura/VR best), Durga Puja (Sep/Oct in Kolkata), Pushkar Camel Fair (Nov Rajasthan), Onam (Aug Kerala boat races), Hornbill Festival (Dec Nagaland). Book travel early and follow local etiquette.",
        "keywords": ["festival", "events", "celebration", "diwali", "holi"]
    },
    {
        "question": "What are the top UNESCO or heritage spots?",
        "answer": "Must-visit heritage circuit: Taj Mahal & Agra Fort, Jaipur's Amer Fort & City Palace, Varanasi Ghats, Khajuraho Temples, Hampi ruins, Ajanta & Ellora caves, Konark Sun Temple, Red Fort Delhi, Qutub Minar, Humayun's Tomb, and Kerala's backwater churches in Fort Kochi.",
        "keywords": ["heritage", "unesco", "monument", "fort", "temple"]
    }
]

FAQ_CONTEXT = "\n\n".join(f"Q: {faq['question']}\nA: {faq['answer']}" for faq in TOURISM_FAQS)


def get_faq_answer(message: str):
    """Return a curated FAQ answer if the user's message matches common topics."""
    text = (message or "").lower()
    for faq in TOURISM_FAQS:
        if any(keyword in text for keyword in faq["keywords"]):
            return faq["answer"]
    return None


def fetch_place_image(place_name):
    """Return a high-resolution thumbnail for the given place using Wikipedia."""
    params = {
        'action': 'query',
        'format': 'json',
        'generator': 'search',
        'gsrsearch': f"{place_name} India",
        'gsrlimit': 1,
        'prop': 'pageimages',
        'piprop': 'thumbnail',
        'pithumbsize': 900,
        'redirects': 1
    }
    headers = {
        'User-Agent': 'NAVIGo/1.0 (contact: info@navigo.com)',
        'Accept': 'application/json'
    }
    try:
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        pages = response.json().get('query', {}).get('pages', {})
        for page in pages.values():
            thumbnail = page.get('thumbnail')
            if thumbnail and thumbnail.get('source'):
                return thumbnail['source']
    except requests.RequestException as exc:
        print(f"⚠️  Wikipedia image lookup failed for {place_name}: {exc}")
    return None


def build_fallback_image(place_name):
    query = quote_plus(f"{place_name} India travel")
    return f"{UNSPLASH_FALLBACK_BASE}{query}"


def resolve_image_url(place_name, fallback_url=None):
    wikipedia_image = fetch_place_image(place_name)
    if wikipedia_image:
        return wikipedia_image
    if fallback_url:
        return fallback_url
    return build_fallback_image(place_name)


def needs_image_refresh(current_url):
    if not current_url:
        return True
    return any(host in current_url for host in OLD_IMAGE_HOSTS)


def refresh_destination_images(force=False):
    """Refresh stored destination images to ensure they match the actual place."""
    updated = 0
    for destination in Destination.query.all():
        if force or needs_image_refresh(destination.image_url):
            new_url = resolve_image_url(destination.name, destination.image_url)
            if new_url != destination.image_url:
                destination.image_url = new_url
                updated += 1
    if updated:
        db.session.commit()
        print(f"🖼️  Updated {updated} destination image(s) with exact matches.")

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    preferences = db.Column(db.String(500))

class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    full_description = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    rating = db.Column(db.Float, default=4.0)
    popularity_score = db.Column(db.Integer, default=0)
    best_time = db.Column(db.String(100))
    state = db.Column(db.String(100))
    ideal_weather = db.Column(db.String(50))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'))
    booking_type = db.Column(db.String(50))
    travel_date = db.Column(db.Date)
    guests = db.Column(db.Integer, default=1)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='confirmed')
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TravelPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    destination_ids = db.Column(db.String(500))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 100 Top Tourist Destinations in India
SAMPLE_DESTINATIONS = [
    # North India - Heritage & Culture
    {"name": "Taj Mahal", "category": "Heritage", "state": "Uttar Pradesh", "lat": 27.1751, "lon": 78.0421, "desc": "Iconic white marble mausoleum", "full_desc": "The Taj Mahal is an ivory-white marble mausoleum built by Mughal emperor Shah Jahan in memory of his wife Mumtaz Mahal. A UNESCO World Heritage Site and one of the New Seven Wonders of the World. Best visited at sunrise or sunset for magical views.", "img": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Agra Fort", "category": "Heritage", "state": "Uttar Pradesh", "lat": 27.1795, "lon": 78.0211, "desc": "Red sandstone Mughal fortress", "full_desc": "A massive red sandstone fort built by Emperor Akbar. This UNESCO World Heritage Site served as the main residence of Mughal emperors. Features stunning palaces, mosques, and gardens with views of Taj Mahal.", "img": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Jaipur Pink City", "category": "Heritage", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "desc": "Royal palaces and vibrant culture", "full_desc": "The capital of Rajasthan, known for its distinctive pink-colored buildings. Home to magnificent forts like Amber Fort, City Palace, Hawa Mahal, and Jantar Mantar observatory. A shopper's paradise for handicrafts and jewelry.", "img": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800", "best_time": "November to February", "ideal_weather": "cool"},
    {"name": "Amber Fort", "category": "Heritage", "state": "Rajasthan", "lat": 26.9855, "lon": 75.8513, "desc": "Majestic hilltop fortress", "full_desc": "Spectacular fort built in red sandstone and marble with stunning mirror work. Elephant rides to the fort entrance are popular. Don't miss the evening light and sound show depicting Rajput history.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Qutub Minar", "category": "Heritage", "state": "Delhi", "lat": 28.5244, "lon": 77.1855, "desc": "Tallest brick minaret in the world", "full_desc": "This 73-meter tall victory tower built in 1193 is a UNESCO World Heritage Site. The complex includes the Iron Pillar, which hasn't rusted in 1600 years. Beautiful Indo-Islamic architecture.", "img": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Red Fort Delhi", "category": "Heritage", "state": "Delhi", "lat": 28.6562, "lon": 77.2410, "desc": "Mughal emperor's palace fortress", "full_desc": "Massive red sandstone fort built by Shah Jahan. Served as the residence of Mughal emperors for 200 years. Independence Day celebrations are held here annually. Features beautiful Mughal gardens and museums.", "img": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Humayun's Tomb", "category": "Heritage", "state": "Delhi", "lat": 28.5933, "lon": 77.2507, "desc": "Magnificent Mughal garden tomb", "full_desc": "First garden-tomb in India, built in 1565. Inspired the construction of Taj Mahal. Stunning Persian-style architecture with beautiful symmetrical gardens. UNESCO World Heritage Site.", "img": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Lotus Temple", "category": "Religious", "state": "Delhi", "lat": 28.5535, "lon": 77.2588, "desc": "Architectural marvel shaped like lotus", "full_desc": "Bahá'í House of Worship with 27 marble petals forming a lotus. Open to all religions for meditation and prayer. Winner of numerous architectural awards. Surrounded by serene pools and gardens.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "India Gate", "category": "Heritage", "state": "Delhi", "lat": 28.6129, "lon": 77.2295, "desc": "War memorial archway", "full_desc": "42-meter tall war memorial commemorating 70,000 Indian soldiers who died in WWI. Resembles Arc de Triomphe. Popular evening picnic spot with illuminated fountain shows.", "img": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Fatehpur Sikri", "category": "Heritage", "state": "Uttar Pradesh", "lat": 27.0945, "lon": 77.6619, "desc": "Abandoned Mughal city", "full_desc": "Built by Akbar in 1571, this red sandstone city was abandoned after 14 years due to water scarcity. UNESCO World Heritage Site showcasing blend of Hindu and Islamic architecture. Features the famous Buland Darwaza.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Rajasthan
    {"name": "Udaipur City of Lakes", "category": "Heritage", "state": "Rajasthan", "lat": 24.5761, "lon": 73.6833, "desc": "Venice of the East", "full_desc": "Known as the most romantic city in India. Famous for Lake Palace, City Palace, boat rides on Lake Pichola. Stunning sunset views and traditional Rajasthani culture. Popular for destination weddings.", "img": "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=800", "best_time": "September to March", "ideal_weather": "cool"},
    {"name": "Jodhpur Blue City", "category": "Heritage", "state": "Rajasthan", "lat": 26.2389, "lon": 73.0243, "desc": "City of blue houses", "full_desc": "Famous for blue-painted houses and massive Mehrangarh Fort. Zip-lining inside the fort is a unique experience. Known for handicrafts, spices, and delicious sweets. Gateway to Thar Desert.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Jaisalmer Golden City", "category": "Heritage", "state": "Rajasthan", "lat": 26.9157, "lon": 70.9083, "desc": "Desert fortress city", "full_desc": "Golden sandstone fort rising from Thar Desert. Living fort with people still residing inside. Camel safaris, desert camping under stars, and traditional Rajasthani folk performances are highlights.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "November to February", "ideal_weather": "cool"},
    {"name": "Pushkar", "category": "Religious", "state": "Rajasthan", "lat": 26.4899, "lon": 74.5511, "desc": "Sacred lake and camel fair", "full_desc": "Holy town with 52 ghats around Pushkar Lake. Home to rare Brahma Temple. Famous annual camel fair in November attracts thousands. Peaceful spiritual atmosphere with beautiful sunset views.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Mount Abu", "category": "Nature", "state": "Rajasthan", "lat": 24.5926, "lon": 72.7156, "desc": "Rajasthan's only hill station", "full_desc": "Cool retreat with Nakki Lake and stunning Dilwara Jain Temples with intricate marble carvings. Sunset Point offers breathtaking views. Popular honeymoon destination.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Uttar Pradesh
    {"name": "Varanasi Ghats", "category": "Religious", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739, "desc": "Oldest living city, spiritual capital", "full_desc": "One of the world's oldest continuously inhabited cities. Witness mesmerizing Ganga Aarti at Dashashwamedh Ghat. Boat rides at sunrise, ancient temples, narrow lanes full of culture. Ultimate spiritual experience.", "img": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Sarnath", "category": "Religious", "state": "Uttar Pradesh", "lat": 25.3773, "lon": 83.0279, "desc": "Where Buddha gave first sermon", "full_desc": "Important Buddhist pilgrimage site where Buddha delivered his first teaching. Features Dhamek Stupa, ancient monasteries, and excellent museum with Ashoka's lion capital.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Lucknow", "category": "Heritage", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "desc": "City of Nawabs", "full_desc": "Famous for Nawabi culture, architecture, and mouth-watering Awadhi cuisine. Must visit Bara Imambara, Chota Imambara, and Rumi Darwaza. Known for tehzeeb (etiquette) and chikankari embroidery.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Mathura Vrindavan", "category": "Religious", "state": "Uttar Pradesh", "lat": 27.4924, "lon": 77.6737, "desc": "Birthplace of Lord Krishna", "full_desc": "Twin holy cities on Yamuna river. Over 5000 temples celebrating Krishna's life. Holi celebrations are spectacular. Visit Banke Bihari Temple, ISKCON temple, and attend evening aarti.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Himachal Pradesh - Mountains
    {"name": "Shimla", "category": "Adventure", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734, "desc": "Queen of Hill Stations", "full_desc": "Former summer capital of British India. Colonial architecture, Mall Road shopping, toy train ride (UNESCO heritage), and scenic mountain views. Perfect for honeymoons and family vacations.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "March to June, December to January", "ideal_weather": "cool"},
    {"name": "Manali", "category": "Adventure", "state": "Himachal Pradesh", "lat": 32.2396, "lon": 77.1887, "desc": "Adventure sports paradise", "full_desc": "Popular honeymoon destination with snow-capped peaks. Offers skiing, paragliding, river rafting, and trekking. Visit Solang Valley, Rohtang Pass, and Hidimba Temple. Vibrant Old Manali cafe culture.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "October to June", "ideal_weather": "cool"},
    {"name": "Dharamshala McLeod Ganj", "category": "Religious", "state": "Himachal Pradesh", "lat": 32.2190, "lon": 76.3234, "desc": "Home of Dalai Lama", "full_desc": "Tibetan culture hub and residence of Dalai Lama. Beautiful monasteries, Tibetan cuisine, yoga retreats, and trekking. Triund trek is very popular. Peaceful mountain town with spiritual vibes.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "March to June, September to December", "ideal_weather": "cool"},
    {"name": "Kullu Valley", "category": "Nature", "state": "Himachal Pradesh", "lat": 31.9578, "lon": 77.1092, "desc": "Valley of Gods", "full_desc": "Picturesque valley along Beas river. Famous for Kullu Dussehra festival, apple orchards, and adventure activities. Base for Great Himalayan National Park treks. Traditional Himachali villages.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "March to June, October to November", "ideal_weather": "cool"},
    {"name": "Spiti Valley", "category": "Adventure", "state": "Himachal Pradesh", "lat": 32.2466, "lon": 78.0317, "desc": "Cold desert mountain valley", "full_desc": "Remote high-altitude valley with Buddhist monasteries and stark landscapes. Visit Key Monastery, Chandratal Lake. Adventure destination for experienced travelers. Road trips through world's highest passes.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "May to October", "ideal_weather": "cool"},
    {"name": "Kasol", "category": "Adventure", "state": "Himachal Pradesh", "lat": 32.0098, "lon": 77.3150, "desc": "Mini Israel of India", "full_desc": "Backpacker's paradise in Parvati Valley. Israeli cafe culture, trekking to Kheerganga, camping by river. Starting point for Tosh and Malana village treks. Hippie vibes and peaceful atmosphere.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "March to June, September to November", "ideal_weather": "cool"},
    {"name": "Dalhousie", "category": "Nature", "state": "Himachal Pradesh", "lat": 32.5448, "lon": 75.9470, "desc": "Colonial hill station", "full_desc": "Quiet hill station named after British Governor-General. Colonial architecture, pine forests, and panoramic mountain views. Visit nearby Khajjiar (Mini Switzerland). Perfect for peaceful retreat.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "March to June, September to November", "ideal_weather": "cool"},
    
    # Uttarakhand - Pilgrimage & Adventure
    {"name": "Rishikesh", "category": "Adventure", "state": "Uttarakhand", "lat": 30.0869, "lon": 78.2676, "desc": "Yoga capital and adventure hub", "full_desc": "World capital of yoga on banks of Ganges. River rafting, bungee jumping, camping. Visit ashrams, attend Ganga Aarti at Triveni Ghat. Beatles Ashram. Gateway to Char Dham yatra. Vegetarian town with spiritual energy.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "September to November, March to May", "ideal_weather": "warm"},
    {"name": "Haridwar", "category": "Religious", "state": "Uttarakhand", "lat": 29.9457, "lon": 78.1642, "desc": "Gateway to Gods", "full_desc": "Ancient holy city where Ganges enters plains. Evening Ganga Aarti at Har Ki Pauri is spectacular. Kumbh Mela held every 12 years. Pilgrimage starting point. Vegetarian food and spiritual shopping.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to February", "ideal_weather": "cool"},
    {"name": "Nainital", "category": "Nature", "state": "Uttarakhand", "lat": 29.3919, "lon": 79.4542, "desc": "Lake District of India", "full_desc": "Beautiful town around Naini Lake surrounded by hills. Boating, Mall Road shopping, ropeway to Snow View. Visit Naina Devi Temple. Colonial architecture. Perfect family hill station.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "March to June, September to November", "ideal_weather": "cool"},
    {"name": "Mussoorie", "category": "Nature", "state": "Uttarakhand", "lat": 30.4598, "lon": 78.0644, "desc": "Queen of Hills", "full_desc": "Popular hill station with stunning views of Doon Valley and Himalayas. Mall Road, Kempty Falls, Gun Hill. Cable car rides and colonial charm. Great for family vacations.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "April to June, September to November", "ideal_weather": "cool"},
    {"name": "Auli", "category": "Adventure", "state": "Uttarakhand", "lat": 30.5200, "lon": 79.5700, "desc": "Skiing paradise", "full_desc": "Premier skiing destination with Asia's longest cable car. Panoramic views of Nanda Devi peak. Artificial lake at 10,000 ft. Summer trekking and winter skiing. Quiet and less commercialized.", "img": "https://images.unsplash.com/photo-1605540436563-5bca919ae766?w=800", "best_time": "January to March (skiing), April to November (sightseeing)", "ideal_weather": "cool"},
    {"name": "Valley of Flowers", "category": "Nature", "state": "Uttarakhand", "lat": 30.7268, "lon": 79.6011, "desc": "UNESCO alpine meadow", "full_desc": "Breathtaking valley with endemic alpine flowers. Trek through colorful meadows with 300+ flower species. UNESCO World Heritage Site. Combine with Hemkund Sahib pilgrimage. Opens only July-September.", "img": "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800", "best_time": "July to September", "ideal_weather": "cool"},
    {"name": "Jim Corbett National Park", "category": "Nature", "state": "Uttarakhand", "lat": 29.5312, "lon": 78.7778, "desc": "India's oldest national park", "full_desc": "First national park in India, established 1936. Famous for Bengal tigers. Jungle safaris, elephant rides, bird watching. Over 600 species of wildlife. Multiple zones for different experiences.", "img": "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=800", "best_time": "November to June", "ideal_weather": "warm"},
    
    # Kashmir - Paradise on Earth
    {"name": "Srinagar Dal Lake", "category": "Nature", "state": "Jammu & Kashmir", "lat": 34.0836, "lon": 74.7979, "desc": "Jewel of Kashmir", "full_desc": "Stay in traditional houseboats on Dal Lake. Shikara rides through floating gardens. Visit Mughal Gardens - Shalimar Bagh, Nishat Bagh. Shopping on floating markets. Gateway to Kashmir valley adventures.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "April to October", "ideal_weather": "cool"},
    {"name": "Gulmarg", "category": "Adventure", "state": "Jammu & Kashmir", "lat": 34.0484, "lon": 74.3805, "desc": "Meadow of flowers, skiing destination", "full_desc": "Asia's highest cable car to 13,000 ft. World-class skiing in winter, gondola rides and flowers in summer. Golf course at 8,700 ft. Stunning views of Nanga Parbat. Adventure sports paradise.", "img": "https://images.unsplash.com/photo-1605540436563-5bca919ae766?w=800", "best_time": "December to March (snow), April to June (flowers)", "ideal_weather": "cool"},
    {"name": "Pahalgam", "category": "Nature", "state": "Jammu & Kashmir", "lat": 34.0161, "lon": 75.3150, "desc": "Valley of shepherds", "full_desc": "Base camp for Amarnath Yatra. Beautiful Lidder river valley. Betaab Valley, Aru Valley nearby. Trekking, fishing, horse riding. Filming location for many Bollywood movies. Pine forests and meadows.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "April to October", "ideal_weather": "cool"},
    {"name": "Sonamarg", "category": "Adventure", "state": "Jammu & Kashmir", "lat": 34.3000, "lon": 75.2900, "desc": "Meadow of Gold", "full_desc": "Gateway to Ladakh via Zoji La Pass. Thajiwas Glacier trek, pony rides, river rafting. Pristine alpine lakes and snow-capped peaks. Stop on Srinagar-Leh highway. Camping under stars.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "May to October", "ideal_weather": "cool"},
    
    # Ladakh - Land of High Passes
    {"name": "Leh Ladakh", "category": "Adventure", "state": "Ladakh", "lat": 34.1526, "lon": 77.5771, "desc": "Land of high passes", "full_desc": "Remote Himalayan region with Buddhist culture. Monasteries, high-altitude lakes (Pangong, Tso Moriri), world's highest motorable roads. Magnetic Hill, Khardung La pass. Bike trips and unique landscapes. Spiritual and adventurous.", "img": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800", "best_time": "May to September", "ideal_weather": "cool"},
    {"name": "Nubra Valley", "category": "Adventure", "state": "Ladakh", "lat": 34.5708, "lon": 77.5605, "desc": "Valley of flowers with sand dunes", "full_desc": "High altitude cold desert with double-humped Bactrian camels. Reached via Khardung La (world's highest motorable road). Diskit Monastery with 100ft Buddha statue. White sand dunes and apricot orchards.", "img": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800", "best_time": "May to September", "ideal_weather": "cool"},
    {"name": "Pangong Lake", "category": "Nature", "state": "Ladakh", "lat": 33.7500, "lon": 78.9000, "desc": "Stunning high-altitude lake", "full_desc": "World-famous blue lake that changes colors. Featured in '3 Idiots' movie. 134 km long, extends to Tibet. Camping by lakeside under starry skies. Challenging but rewarding journey through Chang La pass.", "img": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800", "best_time": "May to September", "ideal_weather": "cool"},
    
    # Punjab & Haryana
    {"name": "Golden Temple Amritsar", "category": "Religious", "state": "Punjab", "lat": 31.6200, "lon": 74.8765, "desc": "Holiest Sikh shrine", "full_desc": "Stunning gold-plated Harmandir Sahib surrounded by sacred pool. World's largest free kitchen (langar) serving 100,000 daily. Beautiful at night with reflection. Wagah Border ceremony nearby. Spiritual experience for all.", "img": "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Chandigarh", "category": "Heritage", "state": "Punjab/Haryana", "lat": 30.7333, "lon": 76.7794, "desc": "Le Corbusier's planned city", "full_desc": "India's first planned city designed by Le Corbusier. Rock Garden, Sukhna Lake, Rose Garden. Clean, organized, with wide roads. Capitol Complex is UNESCO heritage. Modern city with gardens and museums.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Maharashtra - Western India
    {"name": "Mumbai Gateway of India", "category": "Heritage", "state": "Maharashtra", "lat": 18.9220, "lon": 72.8347, "desc": "Iconic arch monument", "full_desc": "Built in 1924 to commemorate King George V's visit. Gateway to India for visitors arriving by sea. Overlooks Arabian Sea with boats to Elephanta Caves. Marine Drive, Colaba Causeway nearby. Symbol of Mumbai.", "img": "https://images.unsplash.com/photo-1566552881560-0be862a7c445?w=800", "best_time": "November to February", "ideal_weather": "warm"},
    {"name": "Ajanta Caves", "category": "Heritage", "state": "Maharashtra", "lat": 20.5519, "lon": 75.7033, "desc": "Ancient Buddhist cave paintings", "full_desc": "UNESCO World Heritage with 30 rock-cut caves dating to 2nd century BCE. Exquisite paintings and sculptures depicting Buddha's life. Masterpiece of Buddhist religious art. Audio guides available.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Ellora Caves", "category": "Heritage", "state": "Maharashtra", "lat": 20.0269, "lon": 75.1795, "desc": "Rock-cut temples of 3 religions", "full_desc": "34 monasteries and temples carved into rock. Represents Buddhism, Hinduism, and Jainism. Kailasa temple (Cave 16) is world's largest monolithic structure. UNESCO World Heritage Site.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Lonavala Khandala", "category": "Nature", "state": "Maharashtra", "lat": 18.7542, "lon": 73.4091, "desc": "Monsoon hill stations", "full_desc": "Twin hill stations near Mumbai and Pune. Lush green in monsoons with waterfalls. Visit Bhaja caves, Tiger's Leap viewpoint. Famous for chikki (sweet). Perfect weekend getaway with cool climate.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "June to September", "ideal_weather": "rainy"},
    {"name": "Mahabaleshwar", "category": "Nature", "state": "Maharashtra", "lat": 17.9243, "lon": 73.6577, "desc": "Strawberry capital of India", "full_desc": "Hill station with 5 rivers, Arthur's Seat viewpoint. Fresh strawberries and cream, chikki. Pratapgad Fort, Venna Lake boating. Colonial architecture and cool climate. Popular honeymoon destination.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "October to June", "ideal_weather": "cool"},
    {"name": "Shirdi", "category": "Religious", "state": "Maharashtra", "lat": 19.7645, "lon": 74.4769, "desc": "Home of Sai Baba", "full_desc": "Pilgrimage town where Sai Baba lived. Daily darshan attracts millions. Peaceful atmosphere, no caste or religion barriers. Visit Dwarkamai mosque, Chavadi. Free food served to all devotees.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Goa - Beach Paradise
    {"name": "North Goa Beaches", "category": "Beach", "state": "Goa", "lat": 15.5530, "lon": 73.7574, "desc": "Party beaches and nightlife", "full_desc": "Baga, Calangute, Anjuna beaches with water sports, beach shacks, flea markets. Famous Saturday Night Market in Arpora. Trance parties, water sports, Portuguese architecture. Vibrant nightlife and seafood.", "img": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800", "best_time": "November to February", "ideal_weather": "warm"},
    {"name": "South Goa Beaches", "category": "Beach", "state": "Goa", "lat": 15.2551, "lon": 73.9630, "desc": "Peaceful pristine beaches", "full_desc": "Palolem, Agonda, Colva beaches - quieter and cleaner. Luxury resorts, dolphin watching, kayaking. Beautiful sunsets, beach yoga. Less crowded than North Goa. Perfect for relaxation.", "img": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800", "best_time": "November to March", "ideal_weather": "warm"},
    {"name": "Old Goa Churches", "category": "Heritage", "state": "Goa", "lat": 15.5007, "lon": 73.9117, "desc": "Portuguese colonial churches", "full_desc": "UNESCO World Heritage churches including Basilica of Bom Jesus (holds St. Francis Xavier's remains). Se Cathedral, Church of St. Francis of Assisi. Beautiful baroque architecture. Rich colonial history.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "November to February", "ideal_weather": "warm"},
    {"name": "Dudhsagar Falls", "category": "Nature", "state": "Goa", "lat": 15.3144, "lon": 74.3144, "desc": "Sea of Milk waterfall", "full_desc": "Four-tiered waterfall on Goa-Karnataka border. 310m height with milky white appearance. Trek through jungle or jeep safari. Best visited in monsoon. Swimming in natural pool at base.", "img": "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800", "best_time": "July to September", "ideal_weather": "rainy"},
    
    # Karnataka - Southern Heritage
    {"name": "Mysore Palace", "category": "Heritage", "state": "Karnataka", "lat": 12.3051, "lon": 76.6551, "desc": "Indo-Saracenic marvel", "full_desc": "Magnificent palace of Wadiyar dynasty. Stunning architecture lit with 100,000 bulbs on Sundays. Durbar Hall, royal weapons, jewelry. Dasara festival celebrations are grand. Beautiful gardens surrounding.", "img": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800", "best_time": "October to February", "ideal_weather": "warm"},
    {"name": "Hampi", "category": "Heritage", "state": "Karnataka", "lat": 15.3350, "lon": 76.4600, "desc": "Ruins of Vijayanagara Empire", "full_desc": "UNESCO site with 1600 monuments spread across boulder-strewn landscape. Virupaksha Temple, Stone Chariot, Royal Enclosure. Rent bicycle to explore. Sunrise at Matanga Hill. Ancient bazaars and aqueducts.", "img": "https://plus.unsplash.com/premium_photo-1697730337612-8bd916249e30?w=800", "best_time": "October to February", "ideal_weather": "cool"},
    {"name": "Coorg", "category": "Nature", "state": "Karnataka", "lat": 12.3375, "lon": 75.8069, "desc": "Scotland of India", "full_desc": "Coffee plantations, misty hills, waterfalls. Abbey Falls, Raja's Seat viewpoint. Dubare Elephant Camp, Namdroling Monastery. Coorg coffee and honey. Trekking, river rafting. Pleasant climate year-round.", "img": "https://images.unsplash.com/photo-1587049352846-4a222e784acc?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    {"name": "Bangalore Cubbon Park", "category": "Heritage", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "desc": "Garden City IT hub", "full_desc": "India's Silicon Valley with pleasant climate. Lalbagh Botanical Garden, Bangalore Palace, Vidhana Soudha. Thriving cafe culture, pubs, shopping. Nandi Hills sunrise nearby. Cosmopolitan city with gardens.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to February", "ideal_weather": "warm"},
    {"name": "Gokarna", "category": "Beach", "state": "Karnataka", "lat": 14.5479, "lon": 74.3198, "desc": "Laid-back beach town", "full_desc": "Quieter alternative to Goa. Om Beach, Paradise Beach, Half Moon Beach. Mahabaleshwara Temple. Beach camping, yoga retreats. Popular with backpackers. Beautiful sunset views from clifftops.", "img": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    
    # Kerala - God's Own Country
    {"name": "Munnar Tea Gardens", "category": "Nature", "state": "Kerala", "lat": 10.0889, "lon": 77.0595, "desc": "Tea estate hills", "full_desc": "Rolling hills covered in tea plantations. Eravikulam National Park (Nilgiri Tahr), Tea Museum. Mattupetty Dam, Echo Point. Cool climate, scenic viewpoints. Honeymoon paradise. Tea factory tours available.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "September to May", "ideal_weather": "cool"},
    {"name": "Alleppey Backwaters", "category": "Nature", "state": "Kerala", "lat": 9.4981, "lon": 76.3388, "desc": "Venice of East", "full_desc": "Stay in traditional houseboats through palm-fringed canals. Kerala cuisine served onboard. Village life observation, coir making, toddy tapping. Nehru Trophy snake boat race in August. Tranquil and romantic.", "img": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800", "best_time": "November to February", "ideal_weather": "warm"},
    {"name": "Kumarakom Bird Sanctuary", "category": "Nature", "state": "Kerala", "lat": 9.6177, "lon": 76.4280, "desc": "Backwater bird paradise", "full_desc": "14-acre sanctuary on Vembanad Lake banks. Migratory birds from Siberia. Houseboat stays, fishing, Ayurvedic treatments. Peaceful backwater village. Best for bird watching November to February.", "img": "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=800", "best_time": "November to February", "ideal_weather": "warm"},
    {"name": "Kochi Fort Cochin", "category": "Heritage", "state": "Kerala", "lat": 9.9312, "lon": 76.2673, "desc": "Queen of Arabian Sea", "full_desc": "Colonial heritage with Dutch, Portuguese, British influences. Chinese fishing nets, St. Francis Church, Mattancherry Palace. Jew Town, spice markets. Kathakali dance performances. Contemporary art scene.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Wayanad", "category": "Nature", "state": "Kerala", "lat": 11.6854, "lon": 76.1320, "desc": "Hill station with wildlife", "full_desc": "Spice plantations, waterfalls, caves. Chembra Peak trek (heart-shaped lake), Edakkal Caves (prehistoric carvings). Wildlife sanctuaries. Zipline adventures. Cool climate retreat.", "img": "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800", "best_time": "October to May", "ideal_weather": "cool"},
    {"name": "Varkala Beach", "category": "Beach", "state": "Kerala", "lat": 8.7379, "lon": 76.7163, "desc": "Cliff beach with springs", "full_desc": "Only cliff beach in Kerala with natural springs. Janardhana Temple (2000 years old). Yoga centers, Ayurvedic treatments. Less commercialized, hippie vibe. Stunning sunset views from clifftop cafes.", "img": "https://images.unsplash.com/photo-1598948485421-33a1655d3c18?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Kovalam Beach", "category": "Beach", "state": "Kerala", "lat": 8.4004, "lon": 76.9790, "desc": "Crescent beach with lighthouse", "full_desc": "Three crescent beaches - Lighthouse, Hawa, Samudra. Catamaran rides, Ayurvedic massages. Famous red-striped lighthouse. Water sports, seafood. Near Trivandrum airport.", "img": "https://images.unsplash.com/photo-1598948485421-33a1655d3c18?w=800", "best_time": "September to March", "ideal_weather": "warm"},
    {"name": "Thekkady Periyar", "category": "Nature", "state": "Kerala", "lat": 9.5948, "lon": 77.1578, "desc": "Tiger reserve and spice gardens", "full_desc": "Periyar Tiger Reserve with boat safaris on lake. Elephant rides, bamboo rafting, spice plantation tours. Tribal village visits. Cool climate. Best for wildlife viewing October to April.", "img": "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=800", "best_time": "September to May", "ideal_weather": "cool"},
    
    # Tamil Nadu - Temples & Culture
    {"name": "Meenakshi Temple Madurai", "category": "Religious", "state": "Tamil Nadu", "lat": 9.9195, "lon": 78.1193, "desc": "Colorful temple city", "full_desc": "Ancient temple with 14 colorful gopurams covered in sculptures. 33,000 sculptures inside. Evening ceremony at temple. Madurai is 2500 years old. Famous for jasmine flowers and filter coffee.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Rameswaram", "category": "Religious", "state": "Tamil Nadu", "lat": 9.2876, "lon": 79.3129, "desc": "Island pilgrimage", "full_desc": "Sacred island connected by Pamban Bridge. Ramanathaswamy Temple with longest corridor in India. 22 holy wells. Ram Setu (Adam's Bridge). APJ Abdul Kalam memorial. Important Char Dham pilgrimage site.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to April", "ideal_weather": "warm"},
    {"name": "Kanyakumari", "category": "Beach", "state": "Tamil Nadu", "lat": 8.0883, "lon": 77.5385, "desc": "Southernmost tip of India", "full_desc": "Where three oceans meet - Arabian Sea, Bay of Bengal, Indian Ocean. Vivekananda Rock Memorial, Thiruvalluvar Statue. Sunrise and sunset from same spot. Colorful sand beach. Triveni Sangam point.", "img": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Ooty Nilgiris", "category": "Nature", "state": "Tamil Nadu", "lat": 11.4064, "lon": 76.6932, "desc": "Queen of hill stations", "full_desc": "Colonial hill station with toy train (UNESCO heritage). Botanical gardens, Ooty Lake boating. Tea estates, eucalyptus forests. Dodabetta Peak viewpoint. Cool climate escape. Chocolate and tea shopping.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "April to June, September to November", "ideal_weather": "cool"},
    {"name": "Mahabalipuram", "category": "Heritage", "state": "Tamil Nadu", "lat": 12.6269, "lon": 80.1932, "desc": "Rock-cut monuments by sea", "full_desc": "UNESCO site with Shore Temple, Five Rathas, Arjuna's Penance rock carving. Beach town with stone carving workshops. Pallava dynasty architecture from 7th century. Crocodile bank nearby. Beach and heritage combined.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "November to February", "ideal_weather": "warm"},
    {"name": "Pondicherry", "category": "Heritage", "state": "Puducherry", "lat": 11.9416, "lon": 79.8083, "desc": "French colonial town", "full_desc": "Former French colony with European vibe. French Quarter with colorful houses, cafes, bakeries. Auroville (experimental township). Beach promenade, Aurobindo Ashram. Unique fusion of French and Tamil culture. Cheap liquor.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Thanjavur Big Temple", "category": "Heritage", "state": "Tamil Nadu", "lat": 10.7825, "lon": 79.1313, "desc": "Chola dynasty masterpiece", "full_desc": "UNESCO heritage Brihadeeswarar Temple built in 1010 AD. Tallest temple tower in India. Shadow of tower never falls on ground at noon. Marvel of Chola architecture. Bronze sculpture gallery in palace.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Kodaikanal", "category": "Nature", "state": "Tamil Nadu", "lat": 10.2381, "lon": 77.4892, "desc": "Princess of hill stations", "full_desc": "Star-shaped Kodai Lake, Bryant Park, Coaker's Walk. Pine forests, waterfalls, viewpoints. Cooler than Ooty. Pillar Rocks, Green Valley View. Homemade chocolates and eucalyptus oil. Peaceful hill town.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "April to June, September to October", "ideal_weather": "cool"},
    
    # Andhra Pradesh & Telangana
    {"name": "Tirupati Balaji", "category": "Religious", "state": "Andhra Pradesh", "lat": 13.6288, "lon": 79.4192, "desc": "Richest temple in world", "full_desc": "Lord Venkateswara temple on Tirumala hills. Millions donate hair as offering. Book darshan online to avoid 12+ hour wait. Laddu prasadam is famous. Temple receives ₹650 crore annually. Seven hills surrounding.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "September to February", "ideal_weather": "warm"},
    {"name": "Hyderabad Charminar", "category": "Heritage", "state": "Telangana", "lat": 17.3616, "lon": 78.4747, "desc": "City of pearls and biryani", "full_desc": "400-year-old monument and mosque. Laad Bazaar for bangles, pearls. Famous Hyderabadi biryani and Irani chai. Golconda Fort, Hussain Sagar Lake. Modern IT hub with old-world charm. Ramoji Film City nearby.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to February", "ideal_weather": "warm"},
    {"name": "Araku Valley", "category": "Nature", "state": "Andhra Pradesh", "lat": 18.3273, "lon": 82.8771, "desc": "Hill station with tribal culture", "full_desc": "Scenic train journey through tunnels and bridges. Coffee plantations, Borra Caves (limestone formations). Tribal museum, waterfalls. Cool climate escape from Vizag heat. Bamboo chicken specialty.", "img": "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Odisha - Temple State
    {"name": "Konark Sun Temple", "category": "Heritage", "state": "Odisha", "lat": 19.8876, "lon": 86.0945, "desc": "Chariot-shaped temple", "full_desc": "13th century temple shaped like sun god's chariot with 24 wheels. Intricate erotic sculptures. UNESCO World Heritage Site. Konark Dance Festival in December. Near Chandrabhaga Beach.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Puri Jagannath", "category": "Religious", "state": "Odisha", "lat": 19.8135, "lon": 85.8312, "desc": "Home of Lord Jagannath", "full_desc": "One of four Char Dham pilgrimage sites. Famous Rath Yatra (chariot festival) in June/July. Temple flag always flies opposite to wind. Non-Hindus not allowed inside main temple. Puri beach nearby. Temple prasad is world-famous.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "October to March", "ideal_weather": "warm"},
    {"name": "Chilika Lake", "category": "Nature", "state": "Odisha", "lat": 19.7128, "lon": 85.3220, "desc": "Largest coastal lagoon", "full_desc": "Asia's largest brackish water lagoon. Dolphin watching, bird watching (migratory birds). Boat rides to Kalijai Island temple. Seafood delicacies. Connects to Bay of Bengal. Peaceful natural beauty.", "img": "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800", "best_time": "November to February", "ideal_weather": "cool"},
    
    # West Bengal - Cultural Hub
    {"name": "Darjeeling", "category": "Nature", "state": "West Bengal", "lat": 27.0410, "lon": 88.2663, "desc": "Queen of Himalayas", "full_desc": "Famous for tea gardens and toy train (UNESCO heritage). Tiger Hill sunrise over Kanchenjunga. Happy Valley Tea Estate tours. Peace Pagoda, monasteries. Darjeeling tea and momos. Mall Road shopping. Colonial architecture.", "img": "https://images.unsplash.com/photo-1597081728600-178a1d9b0f6f?w=800", "best_time": "March to May, October to December", "ideal_weather": "cool"},
    {"name": "Sundarbans", "category": "Nature", "state": "West Bengal", "lat": 21.9497, "lon": 89.1833, "desc": "Royal Bengal Tiger habitat", "full_desc": "World's largest mangrove forest, UNESCO World Heritage. Boat safaris for tiger spotting (rare sightings). Crocodiles, dolphins, birds. Village stays. Sajnekhali watchtower. Unique ecosystem. Permit required.", "img": "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=800", "best_time": "September to March", "ideal_weather": "cool"},
    {"name": "Kolkata Victoria Memorial", "category": "Heritage", "state": "West Bengal", "lat": 22.5448, "lon": 88.3426, "desc": "City of Joy", "full_desc": "Colonial capital with Victoria Memorial, Howrah Bridge, Kalighat Temple. Cultural hub - Durga Puja celebrations, Bengali sweets, fish curry rice. Street food paradise. Trams still run. Intellectually vibrant city.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Northeast India
    {"name": "Kaziranga National Park", "category": "Nature", "state": "Assam", "lat": 26.5775, "lon": 93.1711, "desc": "One-horned rhino sanctuary", "full_desc": "UNESCO World Heritage with highest density of tigers. 2/3rd of world's one-horned rhinoceros population. Elephant safaris, jeep safaris. Brahmaputra river views. Best wildlife experience February-April.", "img": "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=800", "best_time": "November to April", "ideal_weather": "cool"},
    {"name": "Shillong", "category": "Nature", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933, "desc": "Scotland of the East", "full_desc": "Hill station with pleasant climate. Umiam Lake, Elephant Falls, Don Bosco Museum. Living root bridges nearby. Music capital of India. Golf courses, Cathedral. Police Bazaar for shopping.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "best_time": "October to June", "ideal_weather": "cool"},
    {"name": "Cherrapunji Mawsynram", "category": "Nature", "state": "Meghalaya", "lat": 25.3000, "lon": 91.7000, "desc": "Wettest places on Earth", "full_desc": "World's highest rainfall. Nohkalikai Falls (India's tallest), living root bridges, caves. Mawsynram village. Lush green landscapes. Best in monsoon but accessible October-May. Trek to double-decker root bridge.", "img": "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800", "best_time": "October to May", "ideal_weather": "rainy"},
    {"name": "Tawang Monastery", "category": "Religious", "state": "Arunachal Pradesh", "lat": 27.5860, "lon": 91.8597, "desc": "Largest monastery in India", "full_desc": "17th century Buddhist monastery at 10,000 ft. Second largest in world after Potala Palace. Stunning mountain views. Dalai Lama was born nearby. Permit required to visit. Tawang War Memorial. Challenging but rewarding journey.", "img": "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?w=800", "best_time": "March to October", "ideal_weather": "cool"},
    {"name": "Majuli Island", "category": "Nature", "state": "Assam", "lat": 26.9504, "lon": 94.2152, "desc": "World's largest river island", "full_desc": "Cultural hub of Assamese neo-Vaishnavite culture. Satras (monasteries), mask-making tradition. River island in Brahmaputra. Unique tribal culture. Migratory birds. Accessed by ferry. Eco-tourism destination.", "img": "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800", "best_time": "October to March", "ideal_weather": "cool"},
    
    # Andaman & Nicobar
    {"name": "Havelock Island", "category": "Beach", "state": "Andaman & Nicobar", "lat": 12.0059, "lon": 92.9974, "desc": "Pristine beaches and diving", "full_desc": "Radhanagar Beach (Asia's best). Scuba diving, snorkeling in crystal-clear waters. Elephant Beach, Kalapathar Beach. Sea-walking, kayaking through mangroves. Luxury resorts and beach huts. Paradise for water sports enthusiasts.", "img": "https://images.unsplash.com/photo-1586359716568-3e1907e4cf9f?w=800", "best_time": "October to May", "ideal_weather": "warm"},
    {"name": "Port Blair Cellular Jail", "category": "Heritage", "state": "Andaman & Nicobar", "lat": 11.6234, "lon": 92.7265, "desc": "Colonial prison island", "full_desc": "Historical cellular jail where freedom fighters were imprisoned. Light and sound show depicts history. Ross Island (British headquarters ruins), North Bay for water sports. Gateway to Andaman islands.", "img": "https://images.unsplash.com/photo-1609920658906-8223bd289001?w=800", "best_time": "October to May", "ideal_weather": "warm"},
    {"name": "Neil Island", "category": "Beach", "state": "Andaman & Nicobar", "lat": 11.8312, "lon": 93.0446, "desc": "Vegetable bowl of Andaman", "full_desc": "Quiet island with Natural Bridge (Howrah Bridge), Bharatpur Beach for snorkeling. Less touristy than Havelock. Cycling around island. Beautiful coral reefs. Laxmanpur Beach sunset. Small and peaceful.", "img": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=800", "best_time": "October to May", "ideal_weather": "warm"},
]

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize database with 100 destinations
def init_db():
    with app.app_context():
        db.create_all()
        
        if Destination.query.count() == 0:
            print("Adding 100 tourist destinations to database...")
            for dest in SAMPLE_DESTINATIONS:
                destination = Destination(
                    name=dest['name'],
                    category=dest['category'],
                    description=dest['desc'],
                    full_description=dest['full_desc'],
                    latitude=dest['lat'],
                    longitude=dest['lon'],
                    image_url=resolve_image_url(dest['name'], dest.get('img')),
                    rating=round(3.5 + (hash(dest['name']) % 15) / 10, 1),
                    popularity_score=hash(dest['name']) % 1000 + 500,
                    best_time=dest['best_time'],
                    state=dest['state'],
                    ideal_weather=dest['ideal_weather']
                )
                db.session.add(destination)
            db.session.commit()
            print(f"✅ Successfully added {Destination.query.count()} destinations!")
        
        # Ensure existing records also point to accurate place-specific images
        refresh_destination_images()

# Routes
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'message': 'Login successful'})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Account created successfully'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html', google_maps_key=GOOGLE_MAPS_API_KEY)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/plan')
@login_required
def plan():
    return render_template('plan.html', google_maps_key=GOOGLE_MAPS_API_KEY)

@app.route('/booking')
@login_required
def booking():
    return render_template('booking.html')

# API Endpoints
@app.route('/api/destinations')
def get_destinations():
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'popularity')
    state = request.args.get('state', 'all')
    weather = request.args.get('weather', 'all')
    
    query = Destination.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if state != 'all':
        query = query.filter_by(state=state)
    
    if weather != 'all':
        query = query.filter_by(ideal_weather=weather)
    
    if sort_by == 'rating':
        query = query.order_by(Destination.rating.desc())
    elif sort_by == 'popularity':
        query = query.order_by(Destination.popularity_score.desc())
    else:
        query = query.order_by(Destination.name)
    
    destinations = query.all()
    
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'category': d.category,
        'description': d.description,
        'full_description': d.full_description,
        'latitude': d.latitude,
        'longitude': d.longitude,
        'image_url': d.image_url,
        'rating': d.rating,
        'popularity': d.popularity_score,
        'best_time': d.best_time,
        'state': d.state,
        'ideal_weather': d.ideal_weather
    } for d in destinations])

@app.route('/api/destination/<int:dest_id>')
def get_destination_detail(dest_id):
    dest = Destination.query.get_or_404(dest_id)
    
    return jsonify({
        'id': dest.id,
        'name': dest.name,
        'category': dest.category,
        'description': dest.description,
        'full_description': dest.full_description,
        'latitude': dest.latitude,
        'longitude': dest.longitude,
        'image_url': dest.image_url,
        'rating': dest.rating,
        'popularity': dest.popularity_score,
        'best_time': dest.best_time,
        'state': dest.state,
        'ideal_weather': dest.ideal_weather
    })

@app.route('/api/weather/<int:dest_id>')
def get_weather(dest_id):
    destination = Destination.query.get_or_404(dest_id)
    
    # Use OpenWeatherMap API
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={destination.latitude}&lon={destination.longitude}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Determine if weather is suitable for visit
            temp = data['main']['temp']
            weather_main = data['weather'][0]['main'].lower()
            
            # Weather suitability logic
            suitable = True
            recommendation = "Perfect time to visit!"
            
            if destination.ideal_weather == 'cool':
                if temp > 30:
                    suitable = False
                    recommendation = "Too hot right now. Visit during October to March."
                elif temp < 10:
                    recommendation = "Cool weather - bring warm clothes!"
            elif destination.ideal_weather == 'warm':
                if temp < 15:
                    suitable = False
                    recommendation = "Too cold. Better during November to February."
                elif temp > 35:
                    recommendation = "Very hot - plan indoor activities."
            elif destination.ideal_weather == 'rainy':
                if 'rain' not in weather_main:
                    suitable = False
                    recommendation = "Dry season. Visit during monsoons for best experience."
            
            return jsonify({
                'temperature': round(temp, 1),
                'description': data['weather'][0]['description'].title(),
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'icon': data['weather'][0]['icon'],
                'suitable': suitable,
                'recommendation': recommendation,
                'feels_like': round(data['main']['feels_like'], 1),
                'pressure': data['main']['pressure']
            })
    except Exception as e:
        print(f"Weather API Error: {e}")
    
    # Fallback weather data
    return jsonify({
        'temperature': 25,
        'description': 'Partly Cloudy',
        'humidity': 65,
        'wind_speed': 10,
        'icon': '02d',
        'suitable': True,
        'recommendation': 'Weather data unavailable. Check ' + destination.best_time,
        'feels_like': 26,
        'pressure': 1013
    })

@app.route('/api/weather-recommendations')
def weather_recommendations():
    """Get destinations based on current weather conditions"""
    try:
        destinations = Destination.query.all()
        recommendations = []
        
        for dest in destinations[:20]:  # Check first 20 for performance
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={dest.latitude}&lon={dest.longitude}&appid={OPENWEATHER_API_KEY}&units=metric"
            
            try:
                response = requests.get(weather_url, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    temp = data['main']['temp']
                    
                    # Match destinations with current good weather
                    if dest.ideal_weather == 'cool' and 15 <= temp <= 28:
                        recommendations.append({
                            'id': dest.id,
                            'name': dest.name,
                            'temperature': round(temp, 1),
                            'weather': data['weather'][0]['description']
                        })
                    elif dest.ideal_weather == 'warm' and 20 <= temp <= 32:
                        recommendations.append({
                            'id': dest.id,
                            'name': dest.name,
                            'temperature': round(temp, 1),
                            'weather': data['weather'][0]['description']
                        })
            except:
                continue
        
        return jsonify(recommendations[:10])  # Return top 10
    except:
        return jsonify([])

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    
    if not message:
        return jsonify({'response': 'Please type a tourism question and I will help!'}), 400
    
    # 1) Try curated FAQ answers for instant responses
    faq_answer = get_faq_answer(message)
    if faq_answer:
        return jsonify({'response': faq_answer, 'source': 'faq'})
    
    # 2) Defer to Gemini for open-ended Indian tourism questions
    if not GEMINI_MODEL:
        return jsonify({
            'response': 'Our AI assistant needs a Gemini API key to answer custom questions. Meanwhile, ask about best time, budgets, safety, food, festivals, or transport and I will share curated tips.',
            'source': 'fallback'
        }), 503
    
    prompt = (
        "You are NAVIGo, an Indian tourism AI assistant. Use the FAQ facts below as your primary knowledge. "
        "If the user requests itinerary ideas, highlight 2-3 relevant Indian destinations with best time, cost hints, and travel tips. "
        "Keep answers under 200 words, use bullet points where it improves readability, and mention safety, culture, or booking tips when relevant. "
        "Never fabricate data—stick to Indian tourism insights.\n\n"
        f"{FAQ_CONTEXT}\n\n"
        f"User question: {message}"
    )
    
    try:
        ai_response = GEMINI_MODEL.generate_content(prompt)
        response_text = getattr(ai_response, "text", None)
        if not response_text:
            # Build text manually if the SDK returns candidates
            parts = []
            for candidate in getattr(ai_response, "candidates", []):
                content = getattr(candidate, "content", None)
                if content and getattr(content, "parts", None):
                    for part in content.parts:
                        text_part = getattr(part, "text", None)
                        if text_part:
                            parts.append(text_part)
            response_text = "\n".join(filter(None, parts)).strip()
        
        if not response_text:
            raise ValueError("Empty response from Gemini")
        
        return jsonify({'response': response_text.strip(), 'source': 'gemini'})
    except Exception as exc:
        print(f"⚠️  Gemini response failed: {exc}")
        return jsonify({
            'response': 'I’m having trouble reaching Gemini right now. Please retry in a moment or ask one of the common tourism questions (best time, budgets, visas, safety, food, transport, festivals).',
            'source': 'error'
        }), 502

@app.route('/api/reviews/<int:dest_id>')
def get_reviews(dest_id):
    reviews = Review.query.filter_by(destination_id=dest_id).order_by(Review.created_at.desc()).limit(10).all()
    
    return jsonify([{
        'id': r.id,
        'rating': r.rating,
        'comment': r.comment,
        'created_at': r.created_at.strftime('%B %d, %Y')
    } for r in reviews])

@app.route('/api/reviews', methods=['POST'])
@login_required
def add_review():
    data = request.get_json()
    
    review = Review(
        user_id=session['user_id'],
        destination_id=data['destination_id'],
        rating=data['rating'],
        comment=data['comment']
    )
    db.session.add(review)
    
    # Update destination rating
    dest = Destination.query.get(data['destination_id'])
    reviews = Review.query.filter_by(destination_id=data['destination_id']).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 4.0
    dest.rating = round(avg_rating, 1)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review added successfully'})

@app.route('/api/bookings', methods=['POST'])
@login_required
def create_booking():
    data = request.get_json()
    
    booking = Booking(
        user_id=session['user_id'],
        destination_id=data['destination_id'],
        booking_type=data['booking_type'],
        travel_date=datetime.strptime(data['travel_date'], '%Y-%m-%d').date(),
        guests=data.get('guests', 1),
        total_amount=data.get('total_amount', 0),
        contact_name=data.get('contact_name', ''),
        contact_phone=data.get('contact_phone', ''),
        contact_email=data.get('contact_email', '')
    )
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Booking confirmed successfully!',
        'booking_id': booking.id,
        'booking_details': {
            'id': booking.id,
            'destination_id': booking.destination_id,
            'type': booking.booking_type,
            'date': booking.travel_date.strftime('%Y-%m-%d'),
            'guests': booking.guests,
            'amount': booking.total_amount,
            'status': booking.status
        }
    })

@app.route('/api/bookings/my')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.created_at.desc()).all()
    
    result = []
    for b in bookings:
        dest = Destination.query.get(b.destination_id)
        result.append({
            'id': b.id,
            'destination': dest.name if dest else 'Unknown',
            'destination_id': b.destination_id,
            'image': dest.image_url if dest else '',
            'type': b.booking_type,
            'date': b.travel_date.strftime('%B %d, %Y'),
            'guests': b.guests,
            'amount': b.total_amount,
            'status': b.status,
            'contact_name': b.contact_name,
            'contact_phone': b.contact_phone,
            'booked_on': b.created_at.strftime('%B %d, %Y')
        })
    
    return jsonify(result)

@app.route('/api/plan/save', methods=['POST'])
@login_required
def save_plan():
    data = request.get_json()
    
    plan = TravelPlan(
        user_id=session['user_id'],
        destination_ids=','.join(map(str, data['destination_ids'])),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    )
    db.session.add(plan)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Travel plan saved successfully'})

@app.route('/api/states')
def get_states():
    """Get list of all states with destination counts"""
    states = db.session.query(
        Destination.state, 
        db.func.count(Destination.id).label('count')
    ).group_by(Destination.state).all()
    
    return jsonify([{'state': s[0], 'count': s[1]} for s in states])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)