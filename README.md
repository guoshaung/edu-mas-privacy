# EduMAS Privacy Learning Platform

![EduMAS Logo](./docs/assets/edumas-logo.svg)

This project is a multi-agent personalized education system for personalized learning, with privacy protection as a core architectural constraint. It focuses on a student-side local privacy gateway and a server-side multi-agent collaboration pipeline, while keeping the current implementation in a prototype stage with several modules already available and several modules still being expanded.

## Project Overview

The platform is designed around a student learning workflow:

- diagnosis
- planning
- tutoring
- assessment
- psychological support in a future stage

The current prototype already includes a unified login page, a student function hub, a guided diagnosis workflow, local persona persistence, and several placeholder or evolving student-side learning modules. Teacher and student interfaces are separated, and the local student persona is not directly exposed to the teacher side.

## Technologies

- `Python 3.12`: local server entry and backend-side prototyping
- `http.server`: lightweight local app launch for demo and integration
- `React`: unified login interface and front-end interaction logic
- `HTML/CSS/JavaScript`: current teacher and student workspace pages
- `localStorage`: browser-side persistence for diagnosis results and local persona data
- `Pydantic`: structured data modeling in Python modules
- `FastAPI` and related backend libraries: reserved in the project dependencies for API expansion
- `NumPy`, `Pandas`, `scikit-learn`: data processing and educational modeling support
- `NetworkX`: graph experimentation support
- `Opacus`: differential privacy experimentation support

## Functional Scope

Implemented or visible in the current prototype:

- unified login for teacher and student roles
- student function hub with four major learning modules
- guided personality and learning diagnosis
- local persona storage and local visualization
- teacher-side and student-side page separation
- privacy-oriented local-first interaction pattern

Planned or partially evolving:

- adaptive learning plan generation
- intelligent tutoring workflow
- knowledge assessment and feedback loop
- privacy gateway enforcement between local student data and cloud agents
- multi-agent orchestration for diagnosis, planning, tutoring, and assessment
- psychological counseling module for student emotional support

## Main Entry

Start the project from the repository root:

```bash
python app.py
```

After startup, open:

```text
http://127.0.0.1:8000/login.html
```

The unified login page lets you choose the teacher side or student side.

## Current Structure

- `app.py`: main local server entry
- `login.html`: unified login page
- `login_app.jsx`: React login logic
- `frontend/`: teacher and student pages
- `gateway/`: privacy gateway and access-control logic
- `protocols/`: shared protocol definitions
- `docs/assets/`: project assets including the logo
- `docs/guides/`: usage and deployment guides
- `docs/reports/`: historical reports and completion records
- `scripts/maintenance/`: helper and verification scripts

## Student Flow

- Unified login
- Student hub
- Personality diagnosis
- Learning planning
- Adaptive tutoring
- Knowledge assessment
- Psychological counseling (planned)

The diagnosis page stores the student profile locally in the browser and keeps the local persona separated from the teacher side.

## Notes

- The root directory has been cleaned to keep only the main entry and core project files.
- Historical reports and auxiliary scripts were moved instead of being left in the root.
- Demo-only Python launchers were removed to avoid multiple competing entry points.
