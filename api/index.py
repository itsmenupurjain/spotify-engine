import sys
import os

# Add root directory to path so 'backend' module is resolvable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Add backend directory to path so internal imports (like 'from app.config') resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Explicitly import from backend so Vercel AST parser includes the folder
from backend.app.main import app
