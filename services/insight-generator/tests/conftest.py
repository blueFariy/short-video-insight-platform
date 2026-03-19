"""
Pytest configuration - adds parent directory to Python path
"""
import sys
from pathlib import Path

# Add the service directory to Python path
service_dir = Path(__file__).parent.parent
sys.path.insert(0, str(service_dir))
