from fastapi import FastAPI, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from models import (
    SessionLocal,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    SportsEvent,
    SportsEventCreate,
    SportsEventUpdate,
    SportsEventResponse,
    get_user_by_email,
    get_user_by_username,
    verify_password,
    get_password_hash,
)
from pathlib import Path
import json

app = FastAPI(
    title="Sports Spotter API",
    description= "API for all sports activities and events available in Muenster",
    version="0.8.0",
    contact={
        "name": "Faith Muchemi and Team",
        "email": "fmuchemi@uni-muenster.de",
    },
    license_info={
        "name": "MIT",
        "url": "https://choosealicense.com/licenses/mit/",
    }
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000"],  # Add your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load GeoJSON data
def load_geojson():
    geojson_path = Path("./data.geojson")
    if not geojson_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GeoJSON file not found",
        )
    with open(geojson_path, "r") as file:
        return json.load(file)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the SportSpotter API!",
        "endpoints": {
            "user_signup": "/api/signup",
            "user_login": "/api/login",
            "events_get_all" : "/api/events",
            "event_create": "/api/events",
            "event_get": "/api/events/{event_id}",
            "event_update": "/api/events/{event_id}",
            "event_delete": "/api/events/{event_id}",
            "sports_locations_get": "/api/sports_geojson"
        }
    }

# Endpoint to serve GeoJSON data
@app.get("/api/sports_geojson")
def get_geojson():
    return load_geojson()



# Routes
@app.post("/api/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if passwords match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # Check if email or username already exists
    if get_user_by_email(db, user.email) or get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create the user
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse.model_validate(db_user)

@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Convert SQLAlchemy object to a dictionary
    user_dict = {
        "id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "is_active": db_user.is_active,
    }

    return {"message": "Login successful", "user": UserResponse.model_validate(user_dict)}

# SportsEvent routes
@app.post("/api/events", response_model=SportsEventResponse)
def create_event(event: SportsEventCreate, db: Session = Depends(get_db)):
    db_event = SportsEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return SportsEventResponse.model_validate(db_event)

@app.get("/api/events/{event_id}", response_model=SportsEventResponse)
def read_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(SportsEvent).filter(SportsEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return SportsEventResponse.model_validate(db_event)

@app.put("/api/events/{event_id}", response_model=SportsEventResponse)
def update_event(event_id: int, event: SportsEventUpdate, db: Session = Depends(get_db)):
    db_event = db.query(SportsEvent).filter(SportsEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Update only the fields that are provided in the request
    update_data = event.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return SportsEventResponse.model_validate(db_event)

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(SportsEvent).filter(SportsEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    db.delete(db_event)
    db.commit()
    return {"message": "Event deleted successfully"}


# Get all events ordered by recent date and time
@app.get("/api/events", response_model=List[SportsEventResponse])
def get_all_events(
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(10, description="Maximum number of items to return"),
    db: Session = Depends(get_db),
):
    # Query events ordered by date (descending) and time (descending)
    db_events = (
        db.query(SportsEvent)
        .order_by(SportsEvent.date.desc(), SportsEvent.time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert SQLAlchemy objects to dictionaries
    events = [
        {
            "id": event.id,
            "title": event.title,
            "location": event.location,
            "date": event.date,
            "time": event.time,
            "tag": event.tag,
        }
        for event in db_events
    ]
    
    # Validate and return the list of events
    return [SportsEventResponse.model_validate(event) for event in events]

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
