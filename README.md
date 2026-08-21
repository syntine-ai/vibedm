# Vibe DM

<p align="center">
  <img src="assets/logo.png" alt="Vibe DM Logo" width="120">
</p>

[![CI Status](https://github.com/syntine-ai/vibedm/actions/workflows/ci.yml/badge.svg)](https://github.com/syntine-ai/vibedm/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Node.js Version](https://img.shields.io/badge/Node.js-20%2B-green.svg)](https://nodejs.org/)

Vibe DM is a modern, open-source, smart **Instagram DM automation platform** built to help creators, brands, and businesses streamline customer interactions, automate direct message workflows, and run campaigns seamlessly. 

This repository is structured as a **monorepo** containing both the backend service and the frontend user interface.

<p align="center">
  <img src="assets/vibedm_preview.png" alt="Vibe DM Preview" width="800">
</p>

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

### 🔑 Environment Configuration

Before running the application, copy the example environment files and configure the parameters:

#### 1. Backend Configuration
Navigate to [`vibedm_backend/`](./vibedm_backend/) and copy the file:
```bash
cp .env.example .env
```
Key configuration settings in `.env`:
*   `DATABASE_URL`: In Docker, this is pre-configured to point to the local database container. For manual host running, set this to `postgresql+asyncpg://postgres:postgres@localhost:54325/postgres`.
*   `SUPABASE_URL` / `SUPABASE_JWT_SECRET`: Used to securely verify frontend authenticated tokens.
*   `INSTAGRAM_APP_ID` / `INSTAGRAM_APP_SECRET`: Obtained from your [Meta Developer Dashboard](https://developers.facebook.com/).
*   `INSTAGRAM_REDIRECT_URI`: The callback URI for OAuth (usually `http://localhost:3000/auth/instagram/callback`).

#### 2. Frontend Configuration
Navigate to [`vibedm_frontend/`](./vibedm_frontend/) and copy the file:
```bash
cp .env.example .env
```
Key configuration settings in `.env`:
*   `VITE_API_URL`: Points to the running backend service (normally `http://localhost:8000`).
*   `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`: Credentials for connecting to your Supabase Auth project.

---

### Option A: Docker Compose Setup (Quickest)

Docker Compose spins up a PostgreSQL database container and automatically initializes the database schemas and tables using the migrations mounted from `./vibedm_frontend/supabase/migrations` (along with a Supabase compatibility shim).

From the root directory, simply run:
```bash
docker compose up --build
```

This starts three services:
1.  **Postgres Database (`vibedm-db`):** Live locally on port `54325`.
2.  **FastAPI Backend (`vibedm-backend`):** Live at `http://localhost:8000`. (Interactive OpenAPI Swagger documentation is available at `http://localhost:8000/docs`).
3.  **Vite Frontend UI (`vibedm-frontend`):** Live at `http://localhost:3000`.

---

### Option B: Manual Local Setup

#### 1. Setup Backend
Navigate to the backend directory:
```bash
cd vibedm_backend
```
Ensure you have the `uv` toolchain installed (or use standard Python pip/virtualenv):
```bash
# Install and sync dependencies
uv sync

# Run the FastAPI server (reloads automatically on code updates)
uv run uvicorn app.main:app --reload
```

In a separate terminal, start the background worker process responsible for executing scheduled tasks and queuing webhook automation runs:
```bash
uv run python -m app.worker
```

#### 2. Setup Frontend
Navigate to the frontend directory:
```bash
cd ../vibedm_frontend
```
Install Node modules and start the development server:
```bash
# Install dependencies
npm install

# Run the development server
npm run dev
```

---

## 🔄 Application Usability & Core Workflows

Once the frontend and backend are running, here is how to use the Vibe DM automation platform:

### 1. Account Signup & Login
* Open your browser and go to `http://localhost:3000/signup`.
* Sign up for an account. Your credentials will be managed by Supabase.
* Once verified, log in at `http://localhost:3000/login`.

### 2. Connect Your Instagram Business Account
* Go to the **Settings** tab.
* Click **Connect Instagram**.
* You will be redirected to Facebook OAuth. Log in using a Facebook account that manages an Instagram Business Account/Page.
* Grant the requested permissions (Access direct messages, read conversations, manage pages).
* Once completed, you will be redirected back, and your connected account will show up under your active workspace.

### 3. Build a DM Automation Flow
* Go to the **Automations** tab.
* Click **Create Automation** (or edit an existing template).
* **Set a Trigger:**
  * E.g., *User Comments on a Post* (you can restrict this to specific posts or look for specific keywords in the comment).
  * E.g., *User Sends a DM* containing a specific trigger phrase (e.g., "INFO").
* **Set an Action:**
  * E.g., *Send Direct Message* with a specific text response and a clickable button/link.
  * E.g., *Ask for Contact Details* (collect the user's email/phone number).
* Turn the toggle status to **Active** to publish your flow.

### 4. Monitor Webhooks and Runs (Testing Automations)
* To receive messages in real time on localhost, configure a webhook tunnel (like **ngrok**) to map to your backend `http://localhost:8000`.
* Enter your ngrok webhook endpoint under the Meta App Dashboard Webhooks section.
* When a test user comments or sends a DM matching your trigger, the Meta webhook sends an event to `/webhooks/instagram` on the backend.
* The backend parses the event, queues a job, and the worker executes the automation action (sending a DM response to the test user).
* View execution logs, success rates, and total clicks on the **Dashboard** page.
* View captured user profiles under the **Contacts** tab.

---

## 🌐 Production Deployment

The frontend of this monorepo is pre-configured to build and run on **Cloudflare Pages** using edge server-side rendering (SSR) supported by `@cloudflare/vite-plugin`.

### Automated Deployment via GitHub Actions

We have provided a GitHub Actions workflow in [`.github/workflows/deploy.yml`](./.github/workflows/deploy.yml) that automatically builds and deploys your frontend to Cloudflare Pages on every push to the `main` branch.

#### To set up the automated deployment pipeline:
1. Go to your GitHub repository settings under **Settings** > **Secrets and variables** > **Actions**.
2. Add the following **Repository Secrets**:
   * `CLOUDFLARE_API_TOKEN`: Your Cloudflare API Token (with permission to edit Cloudflare Pages).
   * `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID (found in the Cloudflare dashboard URL).
   * `VITE_SUPABASE_URL`: Your production Supabase project URL.
   * `VITE_SUPABASE_ANON_KEY`: Your production Supabase anonymous client key.
3. Once these secrets are added, pushing to the `main` branch will automatically build and publish your frontend to a live URL!

---

## 🧪 Linting and Testing

Linting checks and unit tests run automatically on every pull request via GitHub Actions. You can execute them locally before pushing:

*   **Backend Verification:**
    ```bash
    cd vibedm_backend
    uv run pytest        # Run unit tests
    uv run ruff check .  # Lint python code
    uv run mypy app      # Static type analysis
    ```

*   **Frontend Verification:**
    ```bash
    cd vibedm_frontend
    npm run lint         # Lint typescript code
    npm run test         # Run frontend unit tests
    ```

---

## 🤝 Contributing

We welcome contributions from the open-source community!
1. Fork the repository.
2. Create a clean branch (`git checkout -b feature/my-new-feature`).
3. Commit your changes (`git commit -m 'feat: add some feature'`).
4. Push to the branch (`git push origin feature/my-new-feature`).
5. Open a Pull Request on GitHub.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
