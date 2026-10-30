# 🚀 EduGenius AI (Kids Edition) — Team Onboarding & Setup Guide

Welcome to the **EduGenius AI** repository! This document contains the exact steps to clone the project, run the database, start the FastAPI backend, and launch the Angular frontend on Windows.

---

## 📋 Prerequisites

Before you start, make sure you have installed:
1. **Git:** [Download Git for Windows](https://git-scm.com/download/win)
2. **Python 3.11+:** [Download Python](https://www.python.org/downloads/) *(⚠️ Check the box: **"Add python.exe to PATH"** during installation)*
3. **Node.js (v18 or v20 LTS):** [Download Node.js](https://nodejs.org/)
4. **Docker Desktop:** [Download Docker Desktop](https://www.docker.com/products/docker-desktop/) *(Must be open and running for MySQL)*

---

## ⚡ Quickstart Commands (Windows Command Prompt - `cmd.exe`)

### Step 0: Clone the Repository

Open Command Prompt (`cmd.exe`) in the folder where you want your projects:

```cmd
git clone https://github.com/BadrFTW/edugenius-ai.git
cd edugenius-ai
```

---

### Step 1: Start the MySQL Database (Docker)

Make sure **Docker Desktop** is running, then run:

```cmd
docker compose up -d
```

> **Database Details:**
> - **Host:** `localhost:3306`
> - **Database Name:** `edugenius_db`
> - **User:** `root`
> - **Password:** `password`

---

### Step 2: Set Up & Run the Backend (FastAPI)

In the same Command Prompt window:

```cmd
:: 1. Create a Python virtual environment
python -m venv venv

:: 2. Activate the virtual environment
call venv\Scripts\activate.bat

:: 3. Install required Python packages
pip install -r backend\requirements.txt

:: 4. Create your local .env configuration file
copy backend\.env.example backend\.env

:: 5. Run the FastAPI development server
uvicorn app.main:app --app-dir backend --reload
```

- **Backend API URL:** `http://localhost:8000/`
- **Interactive Swagger Documentation:** `http://localhost:8000/docs`

*(Keep this Command Prompt window open so the backend stays running!)*

---

### Step 3: Set Up & Run the Frontend (Angular)

Open a **second Command Prompt window (`cmd.exe`)** and navigate to your cloned repository:

```cmd
cd edugenius-ai\frontend

:: 1. Install Node dependencies
npm install

:: 2. Start the Angular local server
npm start
```

- **Frontend Web Application:** `http://localhost:4200/`

---

## 👥 Module Distribution & Work Directory

To avoid Git merge conflicts, each team member works inside their dedicated backend router and frontend feature folder:

| Module | Responsible Member | Backend Path | Frontend Path |
| :--- | :--- | :--- | :--- |
| **Module 1: AI Smart Auth & Safety** | Member 1 | `backend\app\routers\auth.py` | `frontend\src\app\features\auth\` |
| **Module 2: Kid Lesson Summarizer** | Member 2 | `backend\app\routers\content.py` | `frontend\src\app\features\lessons\` |
| **Module 3: Safe AI Tutor Buddy** | Member 3 | `backend\app\routers\tutor.py` | `frontend\src\app\features\tutor\` |
| **Module 4: Quiz & Feedback Analyzer** | Member 4 | `backend\app\routers\assessment.py` | `frontend\src\app\features\quiz-playground\` |
| **Module 5: Visual Schema & Video Generator** | Member 5 | `backend\app\routers\visuals.py` | `frontend\src\app\features\visual-studio\` |

---

## 🌿 Git Branching Workflow

Before writing any new code:
1. Always pull latest changes from `main`:
   ```cmd
   git checkout main
   git pull origin main
   ```
2. Create your own feature branch:
   ```cmd
   git checkout -b feature/moduleX-description
   ```
3. Commit and push your feature branch:
   ```cmd
   git add .
   git commit -m "feat(moduleX): implement feature description"
   git push -u origin feature/moduleX-description
   ```
4. Open a Pull Request (PR) on GitHub for review!