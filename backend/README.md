# Text-to-CAD Backend

FastAPI backend server that generates 3D CAD models using BadCAD.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
2. Run the server:
```bash
python app.py
```
Or using uvicorn directly:
```bash

```

The server will start on http://localhost:8000

## API Documentation

FastAPI provides automatic API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

- `POST /api/generate` - Generate a 3D model from text prompt
- `GET /api/download/{model_id}` - Download the generated STL file

## Usage

Send a POST request to `/api/generate` with JSON body:
```json
{
  "prompt": "create a cube with a hole"
}
```

Response:
```json
{
  "success": true,
  "model_id": "uuid-here",
  "badcad_code": "# Generated BadCAD code...",
  "message": "Generated model for: \"create a cube with a hole\""
}
```