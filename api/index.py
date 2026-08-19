import os
import sys

# Ensure project root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app, init_db

# Ensure database tables and sample records are initialized on serverless cold start
try:
    init_db()
except Exception as e:
    app.logger.warning(f"Serverless DB init notice: {e}")

# WSGI Middleware to normalize Vercel serverless routing PATH_INFO
class VercelPathFixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Extract the real requested path from Vercel headers
        raw_path = (
            environ.get('HTTP_X_FORWARDED_URI') or
            environ.get('HTTP_X_FORWARDED_URL') or
            environ.get('HTTP_X_VERCEL_PATH') or
            environ.get('HTTP_X_MATCHED_PATH') or
            environ.get('REQUEST_URI') or
            environ.get('RAW_URI') or
            environ.get('PATH_INFO') or
            '/'
        )

        # Separate query string if embedded in raw_path
        if '?' in raw_path:
            path_part, query_part = raw_path.split('?', 1)
            raw_path = path_part
            if not environ.get('QUERY_STRING'):
                environ['QUERY_STRING'] = query_part

        # Strip function prefix (/api/index.py or /api/index)
        if raw_path.startswith('/api/index.py'):
            raw_path = raw_path[len('/api/index.py'):] or '/'
        elif raw_path.startswith('/api/index'):
            raw_path = raw_path[len('/api/index'):] or '/'

        if not raw_path.startswith('/'):
            raw_path = '/' + raw_path

        environ['PATH_INFO'] = raw_path
        environ['SCRIPT_NAME'] = ''

        return self.wsgi_app(environ, start_response)

# Apply middleware to Flask WSGI application
app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

