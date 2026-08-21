# Vibe DM

[![CI Status](https://github.com/syntine-ai/vibedm/actions/workflows/ci.yml/badge.svg)](https://github.com/syntine-ai/vibedm/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Node.js Version](https://img.shields.io/badge/Node.js-20%2B-green.svg)](https://nodejs.org/)

Vibe DM is a modern, open-source, smart **Instagram DM automation platform** built to help creators, brands, and businesses streamline customer interactions, automate direct message workflows, and run campaigns seamlessly. 

This repository is structured as a **monorepo** containing both the backend service and the frontend user interface.

---

## 🚀 Key Features

*   **Automation Dashboard:** Create, manage, and edit customized Instagram DM automation flows.
*   **Instagram OAuth Integration:** Connect Instagram Business accounts securely with guided setups.
*   **Secure Authentication:** User signup, login, and sessions powered by Supabase and Instagram OAuth.
*   **Contacts Management:** Track subscribers, conversation history, and user interactions.
*   **Webhooks System:** Listen to real-time events from Meta/Instagram APIs.
*   **Billing Integration:** Multi-processor support ready for Stripe and Razorpay integrations.
*   **Robust Background Job Queue:** Custom-built PostgreSQL-backed background worker with transactional locking (`FOR UPDATE SKIP LOCKED`) for reliable automation task execution.

---

## 🛠️ Project Structure & Tech Stack

```text
Vibe_DM/
├── .github/workflows/   # CI/CD Workflows (GitHub Actions)
├── vibedm_backend/      # FastAPI Python service
└── vibedm_frontend/     # React, Vite, TanStack Router (Start) UI
```

### Backend (`vibedm_backend`)
*   **Framework:** FastAPI (Python 3.12)
*   **Server:** Uvicorn
*   **Database ORM:** SQLAlchemy (asyncpg for asynchronous PostgreSQL queries)
*   **Package Management:** `uv` toolchain for lightning-fast dependency sync
*   **Formatting/Linting:** Ruff & mypy

### Frontend (`vibedm_frontend`)
*   **Framework:** React 19 & TanStack Start
*   **Router:** TanStack Router (Type-safe file-based routing)
*   **Data Fetching:** TanStack Query (React Query)
*   **Styling:** Tailwind CSS & shadcn/ui components
*   **Backend Integration:** Supabase (Auth, database client)

---

## 💻 Getting Started

You can run the application locally either using **Docker (Recommended)** or by setting up the individual services **Manually**.

### Prerequisite Environment Configuration

Before running, make sure to set up the configuration files. 

1.  **Backend:** Copy [`vibedm_backend/.env.example`](./vibedm_backend/.env.example) to `.env` and fill in Supabase and Meta/Instagram credentials.
2.  **Frontend:** Copy [`vibedm_frontend/.env.example`](./vibedm_frontend/.env.example) to `.env` and fill in your Supabase variables.

---

### Option A: Docker Compose Setup (Quickest)

We provide a pre-configured Docker Compose setup that runs PostgreSQL, the backend API, and the React frontend in containers.

From the root directory, simply run:
```bash
docker compose up --build
```

This starts:
*   **Postgres Database:** Available on port `54322`
*   **FastAPI Backend:** Available at `http://localhost:8000` (Docs at `http://localhost:8000/docs`)
*   **React Frontend:** Available at `http://localhost:3000`

---

### Option B: Manual Local Setup

#### 1. Setup Backend
Navigate to the backend directory:
```bash
cd vibedm_backend
```

Ensure you have the `uv` toolchain installed (or use standard Python pip/virtualenv):
```bash
# Sync dependencies
uv sync

# Run the FastAPI server (reloads on file changes)
uv run uvicorn app.main:app --reload
```

In a separate terminal, start the background worker process:
```bash
uv run python -m app.worker
```

#### 2. Setup Frontend
Navigate to the frontend directory:
```bash
cd ../vibedm_frontend
```

Install node modules and start Vite development server:
```bash
# Install dependencies
npm install

# Run the dev server
npm run dev
```

The UI should now be active at `http://localhost:3000/` or `http://localhost:5173/`.

---

## 🧪 Linting and Testing

Both projects are set up with linting and unit tests, which run automatically in our CI pipeline.

*   **Backend Verification:**
    ```bash
    cd vibedm_backend
    uv run pytest
    uv run ruff check .
    uv run mypy app
    ```

*   **Frontend Verification:**
    ```bash
    cd vibedm_frontend
    npm run lint
    npm run test
    ```

---

## 🤝 Contributing

We welcome open-source contributions! If you would like to contribute:
1. Fork this repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
