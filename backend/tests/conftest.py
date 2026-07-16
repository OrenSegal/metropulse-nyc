import sys
from pathlib import Path

# app.main has no data files on disk in CI (they're pipeline outputs, gitignored).
# preload_data() and the JSON loaders in app/main.py already guard every read
# with .exists(), so importing the module here exercises the real no-data path
# rather than a mocked one.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
