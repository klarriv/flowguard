import sys
from pathlib import Path

# Make the repo root importable (packages here are namespace packages with no
# __init__.py, and the package may not be pip-installed in the test env).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
