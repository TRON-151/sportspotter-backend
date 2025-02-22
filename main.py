from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from models import (
    SessionLocal,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserSignupResponse,
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


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")


#JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Default expiration time
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],  # Add your frontend URL here
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

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


# Routes
@app.post("/api/signup", response_model= UserSignupResponse)
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

    # Generate JWT token for the new user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=access_token_expires
    )

    return {
        "message": "User created successfully",
        "user": UserResponse.model_validate(db_user), 
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    #creating a JWT Token
    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": db_user.username},
        expires_delta = access_token_expires
    )

    # Convert SQLAlchemy object to a dictionary
    user_dict = {
        "id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "is_active": db_user.is_active,
    }

    return {
        "message": "Login successful", 
        "user": UserResponse.model_validate(user_dict),
        "access_token": access_token,
        "token_type": "bearer"}

# SportsEvent routes
@app.post("/api/events", response_model=SportsEventResponse)
def create_event(event: SportsEventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    event_data = event.dict()
    event_data["created_bu"] = current_user.id
    
    db_event = SportsEvent(**event.dict(), created_by=current_user.id)
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
def update_event(event_id: int, event: SportsEventUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = db.query(SportsEvent).filter(SportsEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    if db_event.created_by != current_user.id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You are not authorized to update this event",
        )

    # Update only the fields that are provided in the request
    update_data = event.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return SportsEventResponse.model_validate(db_event)

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = db.query(SportsEvent).filter(SportsEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    if db_event.created_by != current_user.id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You are not authorized to delete this event",
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
    try:
        # Query events ordered by date (descending) and time (descending)
        db_events = (
            db.query(SportsEvent)
            .order_by(SportsEvent.date.desc(), SportsEvent.time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Convert SQLAlchemy objects to dictionaries
        # events = [
        #     {
        #         "id": event.id,
        #         "title": event.title,
        #         "location": event.location,
        #         "date": event.date,
        #         "time": event.time,
        #         "tag": event.tag,
        #     }
        #     for event in db_events
        # ]
    
        # Validate and return the list of events
        return db_events
        # return [SportsEventResponse.model_validate(event) for event in db_events]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail = f"Internal server error: {str(e)}"
        )

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
