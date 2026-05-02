import sys
from pathlib import Path

# Vercel runs from project root; smriti lives in src/ layout
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smriti.main import app
