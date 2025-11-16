import os, json, datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("IOA_DB_URL", "sqlite:///./ioa.db")  # default sqlite file in project root
Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Decision(Base):
    __tablename__ = "decisions"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), index=True)
    price = Column(Float)
    sentiment = Column(String(32))
    reason = Column(Text)
    score = Column(Float)
    boosted_score = Column(Float)
    decision = Column(String(32))
    saved = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    raw = Column(JSON, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_decision(record: dict):
    """
    record: dict with keys symbol, price, sentiment, reason, score, boosted_score, decision, saved
    """
    db = SessionLocal()
    try:
        d = Decision(
            symbol=record.get("symbol"),
            price=record.get("price"),
            sentiment=record.get("sentiment"),
            reason=record.get("reason"),
            score=float(record.get("score") or 0),
            boosted_score=float(record.get("boosted_score") or 0),
            decision=record.get("decision"),
            saved=1 if record.get("saved") else 0,
            raw=record
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        return d.id
    finally:
        db.close()

# Optional Mongo helper (if IOA_DB_URL is a mongodb URI, not used by default)
def save_to_mongo(record: dict):
    try:
        from pymongo import MongoClient
        uri = os.getenv("MONGO_URI")
        if not uri:
            return None
        client = MongoClient(uri)
        db = client.get_default_database() if client else None
        coll = db.get_collection("decisions")
        coll.insert_one({**record, "ts": datetime.datetime.utcnow()})
        return True
    except Exception:
        return None
