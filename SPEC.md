# NeuroTutor - Feature Specification

## Project Overview

**NeuroTutor** is an AI-powered tutoring system that adapts LLM responses in real-time based on the student's cognitive state, detected via EEG (Muse/OpenBCI) or webcam-based attention proxies.

## Core Value Proposition

- Real-time detection of student confusion/engagement
- Adaptive LLM explanations that respond to cognitive load
- Hardware-agnostic (EEG or webcam simulator mode)
- Built on research-grade signal processing

---

## Product Requirements

### 1. Cognitive State Detection

#### EEG Mode (Premium)
- **Hardware:** Muse 2 ($220), OpenBCI ($200+)
- **SDK:** BrainFlow
- **Signals:**
  - Cognitive load (alpha/beta/theta ratios)
  - Attention/focus levels
  - Mental fatigue indicators
  - Stress markers
- **Processing:**
  - Band-pass filtering (1-50Hz)
  - Notch filter (50/60Hz)
  - Artifact rejection (eye blink, motion)
  - Spectral feature extraction (FFT, band powers)
  - Real-time classification model

#### Simulator Mode (Default/Free)
- **Webcam-based proxies:**
  - Gaze tracking (dwell time, fixations)
  - Facial expression analysis (confusion, frustration)
  - Mouse movement patterns
  - Keystroke dynamics
  - Self-reported confusion flags
- **No hardware required for pilot**

### 2. LLM Adaptation Engine

#### Input Signals
- Cognitive load score (0-1)
- Attention level (0-1)
- Time on problem (seconds)
- Prior attempts count
- Historical performance

#### Response Adaptations
| Cognitive State | LLM Adjustment |
|-----------------|----------------|
| High confusion | Simplify explanation, add examples |
| Low engagement | Add interactive elements, break topic |
| High cognitive load | Reduce complexity, step-by-step |
| Flow state | Accelerate, introduce challenges |
| Fatigue detected | Suggest break, lighter content |

#### Directive Mapping
```python
DIRECTIVES = {
    "simplify": "Use simpler language, shorter sentences",
    "elaborate": "Add detailed examples and analogies",
    "slow_down": "Break into smaller steps",
    "speed_up": "Move faster, skip basics",
    "encourage": "Add motivational framing",
    "break": "Suggest 5-min break"
}
```

### 3. User Interfaces

#### Student Interface
- Web app (React + FastAPI)
- Mobile responsive
- Real-time cognitive dashboard
- Progress tracking

#### Professor Dashboard
- Class-wide engagement metrics
- At-risk student alerts
- Content effectiveness analytics
- LMS integration (Canvas, Blackboard)

#### Admin Panel
- User management
- Course configuration
- Billing/subscriptions
- Analytics

### 4. Integrations

#### LMS
- Canvas LTI
- Blackboard
- Brightspace
- Moodle

#### Video
- Zoom SDK
- Google Meet
- Microsoft Teams

#### Calendar
- Google Calendar
- Outlook

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
├─────────────────────────────────────────────────────────────┤
│  Student App    │    Professor Dashboard    │   Admin      │
└────────┬────────┴──────────┬───────────────┴──────┬───────┘
         │                   │                        │
         └───────────────────┼────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   FastAPI      │
                    │   Backend      │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐ ┌───────▼───────┐ ┌────────▼────────┐
│ Cognitive State │ │ LLM Gateway   │ │  Analytics      │
│ Processor       │ │ (OpenAI/Mini) │ │  Engine         │
└────────┬────────┘ └────────┬───────┘ └────────┬────────┘
         │                   │                   │
    ┌────▼────┐        ┌─────▼─────┐       ┌────▼────┐
    │ EEG/Muse│        │ LLM APIs  │       │PostgreSQL│
    │ or      │        │            │       │  + Redis │
    │Webcam   │        └───────────┘       └──────────┘
    └─────────┘
```

---

## MVP Features (v1.0)

### Must Have
- [ ] Webcam-based attention detection (simulator mode)
- [ ] Basic LLM directive injection
- [ ] Student-facing web interface
- [ ] Simple professor dashboard (engagement metrics)
- [ ] User authentication (students, professors)
- [ ] Course management

### Should Have
- [ ] EEG integration (Muse)
- [ ] Canvas LTI integration
- [ ] Basic analytics
- [ ] Session history

### Nice to Have
- [ ] Mobile app
- [ ] Real-time video integration
- [ ] Advanced analytics
- [ ] Multi-language support

---

## Pricing Model

| Tier | Price | Features |
|------|-------|----------|
| **Pilot** | Free | 1 course, 50 students, simulator only |
| **Department** | $3,000-5,000/course/semester | Unlimited students, LMS integration, basic EEG |
| **Campus** | $15,000-30,000/year | All courses, SSO, analytics |
| **Research** | $500/course | Data export, IRB support |

---

## Success Metrics

### Student Outcomes
- Test score improvement: +15% (target)
- Time to mastery: -20%
- Engagement increase: +30%

### Product Metrics
- DAU/MAU: 40%+ (students)
- Session duration: 15+ min average
- Confusion resolution rate: 80%+

### Business Metrics
- Customer acquisition cost: <$500/student
- Lifetime value: $2,000+
- Net revenue retention: 120%+

---

## Development Roadmap

### Phase 1: MVP (Weeks 1-4)
- [ ] Webcam attention detection
- [ ] Basic LLM integration
- [ ] Student web app
- [ ] Simple professor dashboard
- [ ] Auth system

### Phase 2: Beta (Weeks 5-8)
- [ ] EEG integration (Muse)
- [ ] Canvas integration
- [ ] Analytics dashboard
- [ ] 5 pilot universities

### Phase 3: Launch (Weeks 9-12)
- [ ] Additional LMS integrations
- [ ] Advanced analytics
- [ ] Mobile web
- [ ] Open for general access

---

## Competitive Advantages

| Competitor | Our Advantage |
|------------|---------------|
| Khanmigo | Real-time biometric adaptation |
| Carnegie Learning | LLM-native, not scripted |
| DreamBox | General purpose, not math-only |
| Duolingo | Deep personalization, higher ed |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| EEG adoption friction | Medium | Lead with simulator mode |
| Privacy concerns | High | FERPA, on-device processing |
| Slow B2B sales | High | Parallel B2C (parents) |
| LLM cost | Medium | Token optimization, caching |

---

_Draft v1.0 - 2026-02-21_
