"""
api/index.py — Vercel serverless entrypoint for the Rural Healthcare App.

Vercel's Python runtime looks for a WSGI-compatible object named `app`.
We import the Flask `app` from the project root.
"""
import sys
import os

# Ensure project root is on sys.path so all local imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
