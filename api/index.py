"""
Vercel serverless entry point for NEURO_PREDICT_SYS.
This file is the entry point for Vercel's Python runtime.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app

# Vercel expects a variable named 'app' at module level
