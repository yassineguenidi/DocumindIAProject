from app.db import SessionLocal
from app.models import Plan

PLANS = [
    ("free", "Free", 10, 5),
    ("starter", "Starter", 100, 10),
    ("business", "Business", 1000, 25),
    ("enterprise", "Enterprise", None, 50),
]

def main():
    db = SessionLocal()
    for code, name, quota, size in PLANS:
        if not db.query(Plan).filter_by(code=code).first():
            db.add(Plan(code=code, name=name, monthly_doc_quota=quota, max_file_size_mb=size))
    db.commit()
    db.close()

if __name__ == "__main__":
    main()