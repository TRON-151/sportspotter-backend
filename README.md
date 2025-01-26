# FastAPI Application with PostgreSQL and GeoJSON Data

This project is a FastAPI application that provides user authentication, sports event management, and serves GeoJSON data. It uses PostgreSQL as the database and is containerized using Docker.

---

## Table of Contents
1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Setup and Run](#setup-and-run)
4. [API Endpoints](#api-endpoints)
5. [Testing the API](#testing-the-api)
6. [Directory Structure](#directory-structure)
7. [Docker Compose](#docker-compose)
8. [License](#license)

---

## Features
- **User Authentication**:
  - Sign up with email, username, and password.
  - Login with email and password.
- **Sports Event Management**:
  - Create, read, update, and delete sports events.
  - Events have a title, location, date, time, and tag (e.g., volleyball, soccer).
- **GeoJSON Data**:
  - Serve GeoJSON data via a GET endpoint.

---

## Prerequisites
- Docker and Docker Compose installed on your machine.
- Basic knowledge of using a terminal.

---

## Setup and Run

### 1. Clone the Repository
```bash
git clone https://github.com/fmuchembi/sportspotter-backend.git
cd sportspotter-backend
```

### 2. Build and Run the Application
Run the following command to start the FastAPI app and PostgreSQL database:

```bash
docker-compose up --build
```

This will:
- Build the FastAPI application Docker image.
- Start a PostgreSQL container.
- Start the FastAPI application container.

### 3. Access the Application
- FastAPI app: `http://localhost:8000`
- PostgreSQL database: `localhost:5440`

---

## API Endpoints

### User Authentication
- **Sign Up**: `POST /signup`
  - Request Body:
    ```json
    {
      "email": "user@example.com",
      "username": "user123",
      "password": "password123",
      "confirm_password": "password123"
    }
    ```

- **Login**: `POST /login`
  - Request Body:
    ```json
    {
      "email": "user@example.com",
      "password": "password123"
    }
    ```

### Sports Event Management
- **Create Event**: `POST /events`
  - Request Body:
    ```json
    {
      "title": "Volleyball Match",
      "location": "Muenster Park",
      "date": "2024-12-25",
      "time": "10:00:00",
      "tag": "volleyball"
    }
    ```

- **Read Event**: `GET /api/events/{event_id}`
- **Update Event**: `PUT /api/events/{event_id}`
- **Delete Event**: `DELETE /api/events/{event_id}`

### GeoJSON Data
- **Get GeoJSON Data**: `GET /geojson`

---

## Testing the API

### 1. Sign Up
```bash
curl -X POST "http://localhost:8000/api/signup" \
-H "Content-Type: application/json" \
-d '{
  "email": "user@example.com",
  "username": "user123",
  "password": "password123",
  "confirm_password": "password123"
}'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "user@example.com",
  "password": "password123"
}'
```

### 3. Create an Event
```bash
curl -X POST "http://localhost:8000/api/events" \
-H "Content-Type: application/json" \
-d '{
  "title": "Volleyball Match",
  "location": "Muenster Park",
  "date": "2025-04-25",
  "time": "10:00:00",
  "tag": "volleyball"
}'
```

### 4. Get GeoJSON Data
```bash
curl -X GET "http://localhost:8000/api/sports_geojson"
```

---

## Directory Structure
```
sportsspotter-backend/
├── app/
│   ├── main.py            # FastAPI app and routes
│   ├── models.py          # Database models and schemas
├── data/
│   ├── data.geojson       # GeoJSON data file
├── Dockerfile             # Dockerfile for the FastAPI app
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
├── README.md              # This file
```

---

## Docker Compose
The `docker-compose.yml` file defines two services:
- **`db`**: PostgreSQL database.
- **`app`**: FastAPI application.

The `app` service depends on the `db` service and waits for it to be healthy before starting.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

---

## Support
For any questions or issues, please open an issue on the GitHub repository.

---
