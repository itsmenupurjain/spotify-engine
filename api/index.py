import sys
import os

# Add the backend directory to the Python path so it can resolve 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
