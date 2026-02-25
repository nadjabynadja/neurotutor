# NeuroTutor — Live Demo Script

A step-by-step guide for demonstrating NeuroTutor to a non-technical audience.
No EEG hardware or API keys required — the app runs fully on simulated data.

---

## Pre-Demo Setup (5 minutes before)

### 1. Install dependencies (first time only)

```bash
# Backend
cd /path/to/neurotutor/backend
pip install -r requirements.txt

# Frontend
cd /path/to/neurotutor/frontend
npm install
```

### 2. Start the backend

```bash
cd backend
python -m api.main
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 3. Start the frontend (new terminal)

```bash
cd frontend
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:3000/
```

### 4. Verify everything is running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "llm_configured": false,
  "simulator_available": true,
  "demo_mode": true
}
```

`"demo_mode": true` means the system is running with simulated cognitive data — no camera needed.

### 5. (Optional) Start a pre-configured demo session

```bash
curl -X POST "http://localhost:8000/demo?scenario=engaged"
```

Save the `session_id` from the response — you can use it to change scenarios mid-demo.

---

## Demo Flow (~10 minutes)

### Step 1 — Open the Student View

Open: **http://localhost:3000**

**What to show:**
- The two-panel layout: cognitive state on the left, chat on the right
- The green "Connected" indicator in the header (WebSocket is live)
- The cognitive state bars updating in real-time with simulated data

**Talking points:**
> "This is what a student sees when they open NeuroTutor. On the left, we're tracking their cognitive state in real-time — attention, cognitive load, engagement, and fatigue. No special hardware required in demo mode; in production this can use webcam analysis or EEG."

---

### Step 2 — Send a first message

Type in the chat: **"Can you explain what recursion is?"**

**What to show:**
- The response adapts based on current cognitive state
- If the student's load is high, the response starts with "Let me walk you through this step by step."
- If they're in flow state (high attention, low load), the response is more direct

**Talking points:**
> "Notice how the response style matches the student's current cognitive state. If they're overloaded, NeuroTutor automatically simplifies. If they're highly engaged, it can push further. This happens automatically — the student doesn't need to ask for it."

---

### Step 3 — Show the directive system

After the response arrives, look at the **Active Adaptations** section on the left panel.

**What to show:**
- Tags like "Simplifying", "Slowing Down", "Encouraging" that appear after a response
- These are the actual directives the system fed into the LLM

**Talking points:**
> "These tags show you what NeuroTutor told the AI tutor to do. There are 10 adaptation modes: simplify, elaborate, slow down, speed up, encourage, suggest a break, summarize, go interactive, add examples, or use analogies. The system picks them automatically."

---

### Step 4 — Simulate a struggling student

Open a new terminal and run:

```bash
# Replace SESSION_ID with the actual session ID shown in the app URL or from /demo response
curl -X POST "http://localhost:8000/simulator/scenario/SESSION_ID?scenario=struggling"
```

Or if using a demo session started in Step 5 of setup:
```bash
curl -X POST "http://localhost:8000/simulator/scenario/demo_XXXXXXXX?scenario=struggling"
```

**What to show (in the browser):**
- Watch the Attention bar drop to ~35%
- Watch the Cognitive Load bar spike to ~85%
- The color of the bars shifts from green → orange → red

Now send another message: **"I still don't get it — can you explain it again?"**

**What to show:**
- The response now opens with "Let me walk you through this step by step."
- Directives update to show "Simplifying" and "Elaborating"

**Talking points:**
> "I've just simulated a student who is struggling — their attention dropped and cognitive load spiked. Watch how the tutor's response automatically shifts to a simpler, more step-by-step approach. The student doesn't have to say 'please explain this more simply' — the system detects it and adapts."

---

### Step 5 — Show the Professor Dashboard

Open: **http://localhost:3000/professor**

**What to show:**
- Three courses in the sidebar (CS101, CS201, CS301)
- At-risk student badges on the sidebar and the alert banner at the top
- Click on **CS101** to load the student list

**What to show in the student list:**
- 8 students, color-coded attention/load/engagement bars
- Students like "David Brown" and "Iris Wang" flagged at-risk (red row)
- The at-risk reasons shown in the alert banner (e.g. "Low attention (<50%)")

- Click the **Analytics** tab to show the 7-day trend charts

**Talking points:**
> "This is what the professor sees. They get a live view of every student's engagement and cognitive load. Students flagged at-risk are highlighted automatically. The professor can see who needs a follow-up office visit, who's in flow, and how engagement is trending over the semester."

---

### Step 6 — Show flow state (optional, if time allows)

```bash
curl -X POST "http://localhost:8000/simulator/scenario/SESSION_ID?scenario=flow"
```

Switch back to the Student View tab.

**What to show:**
- All bars jump green (attention ~90%, load ~40%)
- Send: **"I want to understand the advanced use cases of recursion"**

**Talking points:**
> "This student is in a flow state — optimal learning. NeuroTutor detects this and can accelerate. It won't slow them down with unnecessary simplification."

---

## Key Talking Points

| Feature | What to say |
|---------|-------------|
| **No hardware required** | "Runs fully on webcam simulation — no EEG device needed. Optional EEG integration available for research use." |
| **Real-time adaptation** | "Cognitive state updates every 500ms via WebSocket. Adaptation is invisible to the student." |
| **10 adaptation modes** | "Simplify, elaborate, slow down, speed up, encourage, suggest break, summarize, interactive, examples, analogies." |
| **Professor view** | "Professors see aggregate metrics across their class — who's at risk, who's thriving, how engagement trends week over week." |
| **LLM-agnostic** | "Works with MiniMax, OpenAI, or Anthropic. Set an API key in the environment and restart — no code changes needed." |
| **Privacy-first** | "Cognitive data stays local. No video recorded or uploaded. Only aggregate metrics are stored." |

---

## Unlocking Full AI Responses

By default, the app runs in demo mode with template responses. To enable full LLM-powered responses:

```bash
# Set your MiniMax API key
export MINIMAX_API_KEY=your_key_here

# Restart the backend
python -m api.main
```

Verify with:
```bash
curl http://localhost:8000/health
# "llm_configured": true
```

---

## Scenario Reference

Use these commands to trigger different student states mid-demo:

```bash
# Highly engaged, optimal learning
curl -X POST "http://localhost:8000/simulator/scenario/SESSION_ID?scenario=engaged"

# Struggling — low attention, high load, confused
curl -X POST "http://localhost:8000/simulator/scenario/SESSION_ID?scenario=struggling"

# Flow state — peak performance
curl -X POST "http://localhost:8000/simulator/scenario/SESSION_ID?scenario=flow"

# Fatigued — tiring after long session
curl -X POST "http://localhost:8000/simulator/scenario/SESSION_ID?scenario=fatigued"
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Backend won't start | `pip install fastapi uvicorn numpy opencv-python` |
| Frontend won't start | `npm install` from the `frontend/` directory |
| "Connected" shows red | Make sure backend is running on port 8000 |
| Cognitive bars stay empty | Refresh the page — WebSocket reconnects automatically |
| Chat response is slow | Demo mode uses template responses instantly; API key required for LLM responses |
| Professor dashboard blank | Click a course in the sidebar to load student data |
