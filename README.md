# EduMAS Privacy & Copyright-Aware Learning Platform

<div align="center">

![EduMAS Logo](./docs/assets/edumas-logo.svg)

<br />

![License](https://img.shields.io/badge/License-MIT-f4b400?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Privacy%20Gateway-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-6C5CE7?style=for-the-badge)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-Education%20MAS-1F2A44?style=for-the-badge)
![Privacy](https://img.shields.io/badge/Privacy-SRPG%20Dual%20Stream-17A673?style=for-the-badge)
![Copyright](https://img.shields.io/badge/Copyright-Dynamic%20Compliance-D95C5C?style=for-the-badge)
![FedGNN](https://img.shields.io/badge/FedGNN-Risk%20Modeling-2F80ED?style=for-the-badge)

<br />

**A prototype multi-agent personalized education system with privacy and copyright governance built into the architecture**

</div>

---

## Overview

EduMAS is a research-oriented prototype for personalized education. It combines:

- student-side local interaction and persona storage
- cloud-side multi-agent orchestration
- privacy-first data flow control
- teacher-side copyright-aware resource delivery

The system is organized around a learning workflow:

1. diagnosis
2. planning
3. adaptive tutoring
4. assessment
5. psychological support (future stage)

Unlike a conventional tutoring demo, EduMAS treats **student privacy protection** and **teacher resource copyright protection** as first-class architectural constraints instead of optional afterthoughts.

---

## What Makes This Project Different

### Privacy-side method stack

- **SRPG dual-stream protection**
  splits student input into a logic stream and a privacy stream so that teaching semantics and sensitive student traits can be governed separately.

- **Dynamic privacy trust evaluation**
  \[
  T_{p}(t)=\alpha T_{\text{base}}-\beta D_{t}-\gamma R_{\text{gnn}}-\lambda E_{t}
  \]
  used to control how much student-side data can be safely released at each stage.

- **FedGNN-backed risk modeling**
  tracks communication frequency, temporal behavior, payload size, semantic distribution, and gradient summaries to reconstruct normal behavior patterns and produce a live risk score.

### Copyright-side method stack

- copyright-tagged teacher resource ingestion
- AG4 resource delivery policy control
- dynamic copyright compliance scoring

\[
C_{r}(t)=\mu R_{c}+\nu R_{a}+\xi R_{p}+\rho R_{e}+\sigma R_{i}
\]

This allows the system to decide whether a teacher resource should be:

- delivered as full text
- returned only as a summary
- transformed into substitute/generated material
- fully blocked

### Joint governance layer

Privacy and copyright are scored separately and then fused by a policy layer, enabling decisions such as:

- allow with standard sanitization
- tighten sanitization
- summary-only release
- substitute generation
- block or minimize release

This makes the project easier to describe as a **governance layer on top of a MAS**, rather than as a collection of unrelated security features.

---

## Current Prototype Scope

### Implemented or demo-ready

- unified login for student and teacher roles
- student hub, student profile page, privacy lab, SRPG demo page, algorithm showcase page
- guided diagnosis with local persistence
- planning gateway and LangGraph state machine
- adaptive tutoring flow with AG3 latent strategy skeleton
- assessment flow with AG5 blind-evaluation protocol
- teacher public question bank management
- copyright-aware AG4 delivery policy
- privacy attack demo page
- governance scoring endpoint and frontend display page

### In progress or planned

- deeper psychological support workflow
- stronger SRPG parameter tuning and visualization
- richer teacher document ingestion and formula recognition
- audit dashboards and experiment logs
- watermarking / tracing for teacher-side resources

---

## Tech Stack

### Backend and orchestration

- `Python 3.12`
- `FastAPI`
- `Pydantic`
- `LangGraph`
- `LangChain`
- `Uvicorn`

### ML, graph, and privacy tooling

- `NumPy`
- `PyTorch`
- `scikit-learn`
- `NetworkX`
- `Opacus`

### Frontend and interaction

- `React`
- `HTML / CSS / JavaScript`
- `localStorage`
- `MathJax`

---

## Project Structure

```text
app.py
├─ login.html / login_app.jsx         # unified entry
├─ frontend/                          # student pages, teacher pages, demo views
├─ gateway/                           # privacy gateway, governance scoring, APIs
├─ agents/                            # AG2~AG5 core agent logic
├─ protocols/                         # shared protocol definitions
├─ data/                              # question bank and local demo data
├─ docs/assets/                       # logo and static assets
├─ docs/guides/                       # guides and notes
├─ docs/reports/                      # archived reports
└─ scripts/maintenance/               # verification and maintenance scripts
```

---

## Key Pages

After startup, the main demo pages are:

- `http://127.0.0.1:8000/login.html`
- `http://127.0.0.1:8000/frontend/student_hub.html`
- `http://127.0.0.1:8000/frontend/student_profile.html`
- `http://127.0.0.1:8000/frontend/srpg_demo.html`
- `http://127.0.0.1:8000/frontend/algorithm_showcase.html`
- `http://127.0.0.1:8000/frontend/privacy_lab.html`
- `http://127.0.0.1:8000/frontend/teacher_workspace.html`
- `http://127.0.0.1:8000/frontend/teacher_question_bank.html`

---

## How to Run

### 1. Start the frontend pages

```bash
python app.py
```

Open:

```text
http://127.0.0.1:8000/login.html
```

### 2. Start the 8010 cloud gateway

```bash
.\.venv\Scripts\python.exe deploy\planning_gateway_api.py
```

Health endpoint:

```text
http://127.0.0.1:8010/health
```

---

## Notes

- This is a **research prototype**, not a production-ready commercial deployment.
- Some flows are fully wired while others remain partially simulated for demonstration and thesis prototyping.
- The current codebase is already suitable for demo presentations, architecture discussions, and iterative experimentation around privacy governance, copyright governance, and multi-agent educational workflows.

---

## Suggested Next Directions

- add live parameter tuning for SRPG dual-stream demonstrations
- surface governance scores across more student and teacher views
- add experiment dashboards for \(T_p(t)\), \(C_r(t)\), and joint policy evolution
- deepen AG4 tracing and teacher-resource control
- extend the psychological counseling workflow

