import os
import sys

# Ensure project root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app, init_db

# Ensure database is initialized for serverless environment on cold start
try:
    init_db()
except Exception as e:
    app.logger.warning(f"Serverless DB init notice: {e}")

# Expose WSGI app for Vercel
if __name__ == '__main__':
    app.run()
