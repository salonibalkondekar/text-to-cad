# AI CAD.js - Modular Architecture

A modular AI-powered 3D CAD application that generates 3D models from natural language descriptions.

## 🏗️ Project Structure

```
text-to-cad/
├── backend/                  # Python FastAPI backend (BadCAD integration)
│   ├── app.py               # Backend API server
│   ├── requirements.txt     # Backend dependencies
│   └── ...
├── frontend/                # Frontend (HTML/JS/CSS)
│   ├── index.html           # Main HTML entry point
│   ├── components/          # UI components (header, sidebar, viewport, console)
│   ├── scripts/             # Core JS (ai-generator, cad-engine, three-setup, projects, app)
│   └── styles/              # CSS modules (main, header, sidebar, viewport, console)
├── README.md                # This file
└── ...
```

## 🚀 Getting Started

### 1. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
The backend will run on http://localhost:8000

### 2. Frontend Setup

Open the frontend in your browser or serve it with a local server:

```bash
# Option 1: Direct file
open frontend/index.html

# Option 2: Simple HTTP server
cd frontend
python -m http.server 8000
# Then visit http://localhost:8000
```

---

## 🧩 Component Architecture

### Backend (Python/FastAPI)
- **`app.py`**: Receives prompts, generates BadCAD code, runs BadCAD, returns STL and code
- **`requirements.txt`**: Python dependencies (FastAPI, BadCAD, etc.)

### Frontend (HTML/JS/Three.js)
- **`index.html`**: Main entry point, loads scripts and styles
- **`components/`**: UI modules (header, sidebar, viewport, console)
- **`scripts/`**: Core logic (AI prompt, CAD engine, Three.js setup, templates, app coordinator)
- **`styles/`**: CSS modules for each component

---

## 🎯 Features

- Natural language to 3D model conversion (AI-powered)
- Manual CAD code editing and live preview
- Predefined project templates
- Interactive 3D viewport (Three.js)
- STL download and code display
- Responsive, modular UI
- Backend fallback: If backend is unavailable, local Three.js generation is used

---

## 🔧 Customization

### Add New Object Types (AI)
1. Update pattern recognition in `frontend/scripts/ai-generator.js`
2. Add generator method for new object
3. Register in templates

### Add New Project Templates
- Add to `frontend/scripts/projects.js`

### Styling
- Edit CSS in `frontend/styles/`

---

## 🛠️ Development

### File Loading Order
1. External dependencies (Three.js)
2. Core scripts (CAD engine, AI generator, Three.js setup, projects)
3. Component scripts (header, sidebar, viewport, console)
4. Main app coordinator (app.js)

### Add New Components
1. Create JS in `frontend/components/`
2. Add CSS in `frontend/styles/`
3. Include in `index.html`
4. Initialize in `app.js`

---

## 📝 Usage Examples

### AI Prompts
- "Create a coffee mug with a handle"
- "Design a gear with 12 teeth and a center hole"
- "Make a staircase height 200mm and width 150mm"
- "Build a simple table with 4 legs"

### Manual CAD Code
```javascript
// Create a simple box
const model = cad.cube(2, 2, 2);

// Create a cylinder
const model = cad.cylinder(1, 3);

// Combine objects
const base = cad.cube(3, 0.5, 3);
const pillar = cad.cylinder(0.5, 4);
pillar.mesh.position.y = 2;
const model = base.union(pillar);
```

---

## 🧪 Testing the Workflow

1. **Start the backend server** (see Backend Setup)
2. **Open the frontend** in your browser
3. **Enter a text prompt** in the AI prompt section (e.g., "create a cube with a hole")
4. **Click "Generate 3D Model"**

**Expected Flow:**
1. Frontend sends prompt to backend API
2. Backend generates BadCAD code
3. Backend executes BadCAD and creates STL file
4. Backend returns model ID and BadCAD code
5. Frontend displays BadCAD code in editor
6. Frontend downloads and displays STL model in 3D viewer

**Fallback:** If backend is unavailable, frontend uses local Three.js generation.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes in the appropriate module
4. Test the functionality
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

## 🐳 Docker Deployment

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed

### Quick Start

1. Build and start both backend and frontend:
   ```bash
   docker compose up --build
   ```

2. Access the app:
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000

### Project Structure (Dockerized)
- `backend/Dockerfile` – Python FastAPI backend container
- `frontend/Dockerfile` – Nginx static server for frontend
- `docker-compose.yml` – Orchestrates both services