import inspect
from sqlalchemy.orm import DeclarativeBase

# We can inspect backend/app/models/scientific.py by reading it or importing it if pythonpath is set
import sys
sys.path.insert(0, "backend")

try:
    from app.models import scientific
    models = []
    for name, obj in inspect.getmembers(scientific):
        if inspect.isclass(obj) and hasattr(obj, "__tablename__"):
            models.append((obj.__tablename__, obj))
    print(f"Total tables in scientific.py: {len(models)}")
    for tbl, cls in sorted(models, key=lambda x: x[0]):
        cols = [c.name for c in cls.__table__.columns]
        print(f"  {tbl:30s}: {len(cols)} columns")
except Exception as e:
    print(f"Error importing scientific models: {e}")
