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

## 🚀 Deployment

### Option A: Deploy on Render (recommended)

- **Create a new Web Service** from your GitHub repo
- **Build command**: `pip install -r requirements.txt`
- **Start command**: `gunicorn -b 0.0.0.0:$PORT app:app`
- **Environment variables**:
  - **`SECRET_KEY`**: set a long random value
  - **`OPENWEATHER_API_KEY`**: (optional) for weather
  - **`GEMINI_API_KEY`**: (optional) for chatbot
  - **`GOOGLE_MAPS_KEY`**: (optional) for maps on Home page
  - **`DATABASE_URL`**:
    - Recommended: use Render Postgres and set `DATABASE_URL` to the provided value
    - Simple SQLite (non-production): `sqlite:////var/data/navigo.db` (requires a persistent disk)

Note: if you deploy with **SQLite without a persistent disk**, your data may reset on deploy/restart.

### Option B: Deploy with Docker (any platform that supports containers)

Build and run locally:

```bash
docker build -t navigo-22 .
docker run -p 8000:8000 -e SECRET_KEY="change-me" navigo-22
```

Then deploy the same image to your platform (Render / Railway / Fly.io / etc.).

---

## 📱 Make it an app (Web + Play Store)

### Web app (PWA)

This repo now includes a PWA:
- Manifest: `static/manifest.webmanifest` (served at `/manifest.webmanifest`)
- Service worker: `static/sw.js` (served at `/sw.js`)
- Icons: `static/icons/icon-192.png`, `static/icons/icon-512.png`

After deploying on **HTTPS**, open your site in:
- **Chrome / Edge (desktop)** → install icon in address bar
- **Android Chrome** → menu → **Install app**

### Play Store (recommended): Trusted Web Activity (TWA)

TWA publishes your website as an Android app that loads your **real deployed site** (no rebuild on every web change).

Prereqs:
- Your site must be deployed on **HTTPS** (Render is fine)
- Your PWA must load without major Lighthouse PWA errors

High-level steps:
1. Pick an Android package name, e.g. `com.yourname.navigo`
2. Install Bubblewrap:
   ```bash
   npm i -g @bubblewrap/cli
   ```
3. Initialize a TWA project (run from any folder):
   ```bash
   bubblewrap init --manifest=https://YOUR_DOMAIN/manifest.webmanifest
   ```
4. Build the APK/AAB:
   ```bash
   bubblewrap build
   ```
5. Upload the generated **AAB** to Google Play Console.

Important: **Digital Asset Links**
- To make the TWA fully trusted, your website must host:
  - `/.well-known/assetlinks.json`
- Bubblewrap will tell you exactly what JSON to paste there (depends on your keystore + package name).

---

## 📝 License

MIT License

---

## 👥 Contact

For issues and questions, please open an issue on GitHub.

**Made with ❤️ for travelers exploring India**
