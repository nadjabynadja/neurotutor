# NeuroTutor

AI-powered tutoring system that adapts LLM responses in real-time based on student cognitive state.

## Quick Start

### Prerequisites
- Python 3.10+
- Webcam (for simulator mode)
- Optional: Muse EEG headset

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m api.main
```

The API will run at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:3000`

## Architecture

```
NeuroTutor/
├── backend/
│   ├── api/           # FastAPI endpoints
│   ├── cognitive/     # Attention detection
│   ├── llm/          # Directive engine
│   └── models/       # Data models
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       └── hooks/
└── SPEC.md           # Full specification
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cognitive/start/{session}` | POST | Start tracking |
| `/cognitive/stop/{session}` | POST | Stop tracking |
| `/cognitive/state/{session}` | GET | Get cognitive state |
| `/cognitive/calibrate/{session}` | POST | Calibrate baseline |
| `/directive/analyze` | POST | Get directives |
| `/chat` | POST | Chat with LLM |
| `/ws/cognitive/{session}` | WS | Real-time streaming |

## Modes

### Simulator Mode (Default)
Uses webcam to detect:
- Face presence and position
- Eye contact
- Session duration (fatigue)

### EEG Mode (Premium)
Uses Muse/OpenBCI to detect:
- Cognitive load (alpha/beta/theta)
- Attention levels
- Stress markers

## Environment Variables

```bash
# Optional: For EEG support
BRAINFLOW_TIMEOUT=30

# Optional: For LLM integration
OPENAI_API_KEY=sk-...
MINIMAX_API_KEY=sk-...
```
