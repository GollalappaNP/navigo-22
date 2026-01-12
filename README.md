# 🧭 NAVIGo - Intelligent Tourism System

**NAVIGo** is an intelligent web-based tourism assistant for planning trips across India. It combines curated destination knowledge, real-time weather data, AI-powered chatbot, and interactive itinerary management.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)

---

## ✨ Features

- **100+ Curated Destinations** - Popular Indian tourist spots with rich metadata
- **Advanced Search & Filtering** - By category, state, weather, and ratings
- **Interactive Trip Planning** - Multi-destination planner with route visualization
- **AI-Powered Chatbot** - Gemini AI integration for tourism questions
- **Weather Integration** - Real-time weather data and suitability recommendations
- **Route Optimization** - Automatic waypoint optimization using OSRM
- **User Dashboard** - Save plans, track bookings, and manage reviews

---

## 🛠️ Technologies

**Backend:** Python 3.8+, Flask, SQLAlchemy, SQLite  
**Frontend:** HTML5, CSS3, JavaScript, Leaflet.js  
**APIs:** OpenWeather, OSRM Routing, Wikipedia, Google Gemini

---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "navigo 22"
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (Optional - create `.env` file)
   ```env
   GEMINI_API_KEY=your_api_key_here
   OPENWEATHER_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Run the application**
   ```bash
   python3 app.py
   ```

6. **Access the application**
   Open browser to `http://127.0.0.1:5000`

---

## ⚙️ Configuration

### API Keys

- **OpenWeather API** (Required for weather): Get free key from [openweathermap.org](https://openweathermap.org/api)
- **Gemini API** (Optional for AI chatbot): Get key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Keys can be set in `.env` file or directly in `app.py`

### Database

Uses SQLite by default. Database is auto-initialized on first run with 100+ destinations.

---

## 🚀 Usage

1. **Registration/Login** - Create account or login
2. **Explore Destinations** - Browse, search, and filter destinations
3. **Plan Trip** - Add destinations, set dates, visualize routes
4. **AI Chatbot** - Ask tourism questions via sidebar chatbot
5. **Bookings** - Book destinations and track booking history

---

## 📁 Project Structure

```
navigo 22/
├── app.py                 # Main Flask application
├── requirements.txt       # Dependencies
├── instance/
│   └── navigo.db         # SQLite database
├── static/
│   ├── css/style.css     # Stylesheet
│   └── js/main.js        # JavaScript
└── templates/            # HTML templates
    ├── landing.html
    ├── login.html
    ├── home.html
    ├── dashboard.html
    ├── plan.html
    └── booking.html
```

---

## 📚 API Endpoints

- `GET /api/destinations` - Get all destinations (with filters)
- `GET /api/destination/<id>` - Get destination details
- `GET /api/weather/<id>` - Get weather for destination
- `POST /api/chatbot` - AI chatbot interface
- `POST /api/plan/save` - Save travel plan
- `POST /api/bookings` - Create booking
- `GET /api/bookings/my` - Get user bookings

---

## 🐛 Troubleshooting

**Database issues:** Delete `instance/navigo.db` and restart  
**Weather API:** Check API key and internet connection  
**Gemini chatbot:** Ensure `google-generativeai` is installed  
**Port in use:** Use different port: `flask --app app run --port 5001`

---

## 📝 License

MIT License

---

## 👥 Contact

For issues and questions, please open an issue on GitHub.

**Made with ❤️ for travelers exploring India**
