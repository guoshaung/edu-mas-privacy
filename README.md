# EduMAS Privacy Learning Platform

This project is a multi-agent personalized education system with privacy protection as a core constraint. The repository now uses a single local launch entry for demos and interface development.

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

The diagnosis page stores the student profile locally in the browser and keeps the local persona separated from the teacher side.

## Notes

- The root directory has been cleaned to keep only the main entry and core project files.
- Historical reports and auxiliary scripts were moved instead of being left in the root.
- Demo-only Python launchers were removed to avoid multiple competing entry points.
