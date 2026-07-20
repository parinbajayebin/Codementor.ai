"""
main.py - Render entry point shim
Forwards module import 'main:app' to 'app.main:app'
"""

from app.main import app

__all__ = ["app"]
