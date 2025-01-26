from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from datetime import date, time
from typing import Optional

# Database configuration
DATABASE_URL = "postgresql+psycopg2://postgres:12345@db:5440/sportspotter"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

class SportsEvent(Base):
    __tablename__ = "sports_events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    location = Column(String)
    date = Column(Date)  # Date only
    time = Column(Time)  # Time only
    tag = Column(String)  # e.g., "volleyball", "soccer"

    def __repr__(self):
        return f"<SportsEvent(id={self.id}, title={self.title}, location={self.location})>"

# Pydantic schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True  # Safe serialization without triggering recursion

class SportsEventCreate(BaseModel):
    title: str
    location: str
    date: date  # Date only
    time: time  # Time only
    tag: str

class SportsEventUpdate(BaseModel):
    title: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    #date: Optional[date] = Field(None)  # Date only
    #time: Optional[time] = Field(None)  # Time only
    tag: Optional[str] = Field(None)

class SportsEventResponse(BaseModel):
    id: int
    title: str
    location: str
    date: date  # Date only
    time: time  # Time only
    tag: str

    class Config:
        from_attributes = True  # Safe serialization without triggering recursion

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db, username: str):
    return db.query(User).filter(User.username == username).first()

# Create tables in the database
Base.metadata.create_all(bind=engine)
