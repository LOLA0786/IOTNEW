import os, datetime, json
from sqlalchemy import create_engine, Column, Integer, Float, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DB_URL = os.getenv("IOA_DB_URL","sqlite:///./ioa_full.db")
Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), index=True)
    price = Column(Float)
    sentiment = Column(String(32))
    reason = Column(Text)
    score = Column(Float)
    boosted = Column(Float)
    decision = Column(String(32))
    saved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    strategy = Column(String(64), nullable=True)
    raw = Column(JSON, nullable=True)

class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), index=True)
    qty = Column(Float, default=0.0)
    avg_price = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class PnL(Base):
    __tablename__ = "pnl"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), index=True)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    qty = Column(Float)
    profit = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=datetime.datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="open")
    raw = Column(JSON, nullable=True)

class Portfolio(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), default="default")
    cash = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
