from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# SQLite requires check_same_thread=False for FastAPI
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and ensure required columns exist."""
    Base.metadata.create_all(bind=engine)

    # Auto-migrate existing SQLite schema if columns missing
    try:
        with engine.connect() as conn:
            res = conn.exec_driver_sql("PRAGMA table_info(attendance)").fetchall()
            existing_cols = {row[1] for row in res}
            if existing_cols:
                if "subject" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE attendance ADD COLUMN subject VARCHAR(100) DEFAULT 'General'")
                if "teacher_name" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE attendance ADD COLUMN teacher_name VARCHAR(100) DEFAULT 'Teacher'")
                if "department" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE attendance ADD COLUMN department VARCHAR(100)")
                if "section" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE attendance ADD COLUMN section VARCHAR(50)")
                conn.commit()
    except Exception as e:
        print(f"[DB] Migration check info: {e}")

    # Ensure default administrator exists
    try:
        from backend import crud
        db = SessionLocal()
        try:
            crud.ensure_default_admin(db)
        finally:
            db.close()
    except Exception as e:
        print(f"[DB] Admin check info: {e}")

