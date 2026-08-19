#!/usr/bin/env python3
"""
Initialize the application's database by invoking `init_db()` from `app.py`.
Run: `python3 scripts/init_db.py` from the project root.
"""
import os
import sys

# Ensure project root is on sys.path (works when running from project root)
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import init_db

if __name__ == '__main__':
    init_db()
    print('Database initialization complete.')
