# NAVIGo System Architecture - Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER (Frontend)                        │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Landing    │  │    Login     │  │  Dashboard   │  │  Plan Trip   │   │
│  │    Page      │  │    Page      │  │    Page      │  │    Page      │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
│  ┌──────▼─────────────────▼─────────────────▼─────────────────▼──────┐    │
│  │                    JavaScript Client Logic                          │    │
│  │  • Dynamic destination loading & filtering                          │    │
│  │  • Search & category filters                                       │    │
│  │  • Modal components (destination details, weather)                   │    │
│  │  • Trip plan management (add/remove destinations)                   │    │
│  │  • Map interactions (Leaflet.js)                                   │    │
│  │  • Route calculation & optimization                                │    │
│  │  • Chatbot interface                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      │ HTTP Requests (GET/POST)
                                      │ JSON Responses
                                      │
┌─────────────────────────────────────▼────────────────────────────────────────┐
│                    APPLICATION LAYER (Backend - Flask)                       │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Authentication Module                        │    │
│  │  • /login (POST) - User authentication                              │    │
│  │  • /signup (POST) - User registration                               │    │
│  │  • /logout (GET) - Session termination                              │    │
│  │  • @login_required decorator - Route protection                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                         │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                      RESTful API Endpoints                             │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │  Destination APIs                                             │    │  │
│  │  │  • GET /api/destinations (filter, sort, category, state)      │    │  │
│  │  │  • GET /api/destination/<id> (detailed view)                 │    │  │
│  │  │  • GET /api/states (state list with counts)                   │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │  Weather APIs                                                  │    │  │
│  │  │  • GET /api/weather/<id> (current weather + suitability)      │    │  │
│  │  │  • GET /api/weather-recommendations (best destinations now)    │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │  Planning & Booking APIs                                      │    │  │
│  │  │  • POST /api/plan/save (save travel plan)                     │    │  │
│  │  │  • POST /api/bookings (create booking)                        │    │  │
│  │  │  • GET /api/bookings/my (user's bookings)                   │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │  Review APIs                                                   │    │  │
│  │  │  • GET /api/reviews/<id> (destination reviews)                │    │  │
│  │  │  • POST /api/reviews (add review)                             │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │  AI Chatbot API                                                │    │  │
│  │  │  • POST /api/chatbot (FAQ matching + Gemini integration)      │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                         │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                    External Service Integrations                       │  │
│  │                                                                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │  OpenWeather │  │     OSRM     │  │    Gemini    │                │  │
│  │  │     API      │  │   Routing    │  │     API      │                │  │
│  │  │              │  │    Service   │  │              │                │  │
│  │  │  • Current   │  │  • Route     │  │  • FAQ       │                │  │
│  │  │    weather   │  │    calc      │  │    matching  │                │  │
│  │  │  • Temp,     │  │  • Trip      │  │  • LLM       │                │  │
│  │  │    humidity  │  │    optimize  │  │    queries   │                │  │
│  │  │  • Suitability│  │  • Distance │  │              │                │  │
│  │  │    logic     │  │    & time    │  │              │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      │ ORM Queries (SQLAlchemy)
                                      │ Database Operations
                                      │
┌─────────────────────────────────────▼────────────────────────────────────────┐
│                         DATA LAYER (SQLite Database)                          │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Database Models (SQLAlchemy)                      │    │
│  │                                                                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │     User     │  │ Destination  │  │    Review    │              │    │
│  │  │              │  │              │  │              │              │    │
│  │  │ • id         │  │ • id         │  │ • id         │              │    │
│  │  │ • username   │  │ • name       │  │ • user_id    │              │    │
│  │  │ • email      │  │ • category   │  │ • dest_id    │              │    │
│  │  │ • password   │  │ • state      │  │ • rating     │              │    │
│  │  │ • created_at │  │ • lat/lon    │  │ • comment    │              │    │
│  │  │ • preferences│  │ • image_url  │  │ • created_at │              │    │
│  │  │              │  │ • rating     │  │              │              │    │
│  │  │              │  │ • popularity │  │              │              │    │
│  │  │              │  │ • best_time  │  │              │              │    │
│  │  │              │  │ • ideal_weather│              │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │                                                                       │    │
│  │  ┌──────────────┐  ┌──────────────┐                                 │    │
│  │  │   Booking    │  │ TravelPlan   │                                 │    │
│  │  │              │  │              │                                 │    │
│  │  │ • id         │  │ • id         │                                 │    │
│  │  │ • user_id    │  │ • user_id    │                                 │    │
│  │  │ • dest_id    │  │ • dest_ids   │                                 │    │
│  │  │ • type       │  │ • start_date │                                 │    │
│  │  │ • date       │  │ • end_date   │                                 │    │
│  │  │ • guests     │  │ • created_at │                                 │    │
│  │  │ • amount     │  │              │                                 │    │
│  │  │ • status     │  │              │                                 │    │
│  │  └──────────────┘  └──────────────┘                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                         │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                    Database Initialization                            │  │
│  │  • init_db() - Creates tables on first run                            │  │
│  │  • Seeds ~100 Indian destinations from SAMPLE_DESTINATIONS            │  │
│  │  • Auto-refreshes destination images via Wikipedia API                 │  │
│  │  • Calculates ratings & popularity scores                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                          DETAILED REQUEST FLOW
═══════════════════════════════════════════════════════════════════════════════

1. USER EXPLORATION FLOW
   ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
   │  User   │────▶│ Frontend │────▶│  Flask   │────▶│ Database │
   │ Browser │     │   JS     │     │   API    │     │ (SQLite) │
   └─────────┘     └──────────┘     └──────────┘     └──────────┘
                          │                │                │
                          │                │                │
                          ▼                ▼                ▼
                    Display grid    GET /api/destinations  Query
                    with filters    ?category=Heritage      Destination
                    & search       &state=Rajasthan        table
                                   &sort=popularity

2. WEATHER-AWARE RECOMMENDATION FLOW
   ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐
   │  User   │────▶│ Frontend │────▶│  Flask   │────▶│ OpenWeather  │
   │ Browser │     │   JS     │     │   API    │     │     API      │
   └─────────┘     └──────────┘     └──────────┘     └──────────────┘
                          │                │                │
                          │                │                │
                          ▼                ▼                ▼
                    Show weather    GET /api/weather/<id>  Fetch current
                    cards with     (lat, lon)             weather data
                    temp & icon    + suitability logic    (temp, humidity)

3. TRIP PLANNING FLOW
   ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐
   │  User   │────▶│ Frontend │────▶│  Flask   │────▶│     OSRM     │
   │ Browser │     │   JS     │     │   API    │     │   Routing    │
   └─────────┘     └──────────┘     └──────────┘     └──────────────┘
                          │                │                │
                          │                │                │
                          ▼                ▼                ▼
                    Add destinations  POST /api/plan/save   Calculate
                    → Calculate route  (dest_ids, dates)    route &
                    → Show on map      → Save to DB         optimize
                    → Optimize route   → Return saved ID    waypoints

4. AI CHATBOT FLOW
   ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐
   │  User   │────▶│ Frontend │────▶│  Flask   │────▶│   Gemini     │
   │ Browser │     │   JS     │     │   API    │     │     API      │
   └─────────┘     └──────────┘     └──────────┘     └──────────────┘
                          │                │                │
                          │                │                │
                          ▼                ▼                ▼
                    Send question   POST /api/chatbot    Generate
                    → Display       (message)            response
                    response        → Check FAQ first     with context
                                    → If no match,        (FAQ corpus)
                                    call Gemini

5. BOOKING FLOW
   ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
   │  User   │────▶│ Frontend │────▶│  Flask   │────▶│ Database │
   │ Browser │     │   JS     │     │   API    │     │ (SQLite) │
   └─────────┘     └──────────┘     └──────────┘     └──────────┘
                          │                │                │
                          │                │                │
                          ▼                ▼                ▼
                    Fill booking    POST /api/bookings   Insert into
                    form → Submit   (dest_id, date,      Booking
                    → View booking  guests, amount)       table
                    confirmation    → Return booking ID   → Update
                                                          destination
                                                          rating if
                                                          review added


═══════════════════════════════════════════════════════════════════════════════
                          COMPONENT INTERACTIONS
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Frontend Components                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Landing Page                                                                │
│    ├─ Hero section with CTA                                                 │
│    ├─ Feature highlights                                                     │
│    └─ Preview destinations carousel                                          │
│                                                                               │
│  Dashboard/Home Page                                                          │
│    ├─ Search bar (real-time filtering)                                      │
│    ├─ Category/State/Weather filters                                         │
│    ├─ Destination grid (cards with images)                                   │
│    ├─ Weather recommendations section                                        │
│    └─ Modal: Destination details + embedded map                              │
│                                                                               │
│  Plan Trip Page                                                               │
│    ├─ Destination search & add interface                                     │
│    ├─ Selected destinations sidebar                                          │
│    ├─ Date pickers (start/end)                                               │
│    ├─ Trip summary (duration, distance, budget)                             │
│    ├─ Route map (Leaflet.js)                                                 │
│    ├─ Route optimization button                                              │
│    └─ Action buttons (save, book, share, download)                            │
│                                                                               │
│  Booking Page                                                                 │
│    ├─ Booking form (destination, date, guests)                               │
│    ├─ Contact information fields                                              │
│    └─ Booking history list                                                    │
│                                                                               │
│  Chatbot Sidebar (All Pages)                                                  │
│    ├─ Chat interface                                                          │
│    ├─ Message history                                                         │
│    └─ FAQ suggestions                                                         │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Backend Components                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Authentication Module                                                       │
│    ├─ Password hashing (Werkzeug)                                            │
│    ├─ Session management                                                     │
│    └─ Route protection decorator                                             │
│                                                                               │
│  Destination Management                                                      │
│    ├─ CRUD operations                                                        │
│    ├─ Filtering & sorting logic                                              │
│    ├─ Image URL resolution (Wikipedia API)                                  │
│    └─ Popularity/rating calculations                                         │
│                                                                               │
│  Weather Integration                                                         │
│    ├─ OpenWeather API client                                                 │
│    ├─ Suitability rules engine                                               │
│    └─ Recommendation algorithm                                                │
│                                                                               │
│  AI Chatbot Engine                                                           │
│    ├─ FAQ keyword matcher                                                    │
│    ├─ Gemini API client                                                      │
│    ├─ Prompt engineering (context injection)                                 │
│    └─ Response formatting                                                    │
│                                                                               │
│  Planning & Booking Logic                                                    │
│    ├─ Plan persistence                                                        │
│    ├─ Booking creation                                                       │
│    ├─ Review aggregation                                                     │
│    └─ Budget estimation                                                      │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         External Services                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  OpenWeather API                                                              │
│    └─ Current weather data (temp, humidity, wind, conditions)                │
│                                                                               │
│  OSRM Routing Service                                                         │
│    ├─ Route calculation (driving directions)                                 │
│    └─ Trip optimization (waypoint reordering)                                 │
│                                                                               │
│  Wikipedia API                                                                │
│    └─ Destination image thumbnails                                           │
│                                                                               │
│  Google Gemini API                                                            │
│    └─ Natural language understanding & generation                            │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                          DATA FLOW SUMMARY
═══════════════════════════════════════════════════════════════════════════════

1. User Request → Frontend JS → Flask Route → Database Query → JSON Response
2. User Question → Frontend JS → Flask Chatbot → FAQ Check → Gemini (if needed)
3. Destination Selection → Frontend JS → OSRM API → Route Data → Map Display
4. Weather Query → Frontend JS → Flask Route → OpenWeather API → Suitability Logic
5. Booking Submission → Frontend JS → Flask Route → Database Insert → Confirmation




