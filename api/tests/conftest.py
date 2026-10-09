import os

# db.py reads these when it's imported. Placeholders are enough for tests that
# never touch a database, and they guarantee a test can't reach a real one by
# accident.
for name in ("FLASK_SOURCE_DB", "FLASK_DB"):
    os.environ.setdefault(f"{name}_HOST", "unused.invalid")
    os.environ.setdefault(name, "unused")
    os.environ.setdefault(f"{name}_USER", "unused")
    os.environ.setdefault(f"{name}_PASSWORD", "unused")
