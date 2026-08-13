# 🚀 TaskFlow2 – AI Assisted Task Management Platform

TaskFlow2 is a modern AI-assisted task management platform built with **FastAPI, SQLAlchemy, MySql, HTML, CSS, and Vanilla JavaScript**.

The application allows users to manage projects and tasks while using an offline AI module to automatically generate task details from natural language input.

---

# ✨ Features

## 🔐 Authentication

- User Registration
- User Login
- JWT Authentication
- Protected API Routes

---

## 📋 Task Management

- Create Task
- Update Task
- Delete Task
- View Tasks
- Assign Tasks to Projects
- Due Date Support
- Priority Levels
  - High
  - Medium
  - Low

---

## 📁 Project Management

- Create Project
- Update Project
- Delete Project
- View Project Statistics
- Task Count per Project

---

## 🤖 AI Assisted Task Creation

TaskFlow2 includes an **offline AI parser** (Mock AI).

Users can simply type:

> Learn Docker in 3 days

and the AI automatically generates:

- Smart Title
- Meaningful Description
- Priority
- Due Date Hint

No external API or internet connection is required.

---

## 🔍 Search Algorithms

Two searching algorithms are implemented.

### Linear Search

- Searches tasks sequentially
- Suitable for small datasets

### Binary Search

- Searches sorted task titles
- Faster than Linear Search

---

## 📊 Priority Sorting

Tasks can be sorted by priority.

Priority order:

```
Low
Medium
High
```

Sorting is implemented using:

- Python Insertion Sort

---

## 📈 Dashboard

Dashboard displays:

- Total Tasks
- High Priority Tasks
- Medium Priority Tasks
- Low Priority Tasks
- Total Projects
- Recent Tasks

---

## 💾 Local Storage Cache

The frontend caches data for:

- Faster UI updates
- Reduced API requests
- Better user experience

---

# 🏗 Architecture

```
Frontend
        │
        ▼
Vanilla JavaScript
        │
 REST API
        │
        ▼
FastAPI Backend
        │
        ▼
SQLAlchemy ORM
        │
        ▼
MySql Database
```

---

# 🧠 AI Module

The AI module is completely offline.

Location:

```
backend/ai/mock_parser.py
```

Responsibilities:

- Extract Title
- Generate Description
- Detect Priority
- Detect Due Date
- Normalize Input
- Rule-based NLP Parsing

---

# ⚙ Algorithms Used

### Searching

- Linear Search
- Binary Search

### Sorting

- Insertion Sort

---

# 🛠 Tech Stack

## Backend

- Python 3
- FastAPI
- SQLAlchemy ORM
- MySql
- Pydantic
- JWT Authentication

## Frontend

- HTML5
- CSS3
- Vanilla JavaScript (ES6)

## Database

- MySql

---

# 📂 Folder Structure

```
TaskFlow2
│
├── backend
│   ├── ai
│   │   └── mock_parser.py
│   ├── auth.py
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   ├── middleware.py
│   ├── models.py
│   ├── projects.py
│   ├── schemas.py
│   ├── tasks.py
│   └── validators.py
│
├── frontend
│   ├── index.html
│   ├── login.html
│   ├── script.js
│   ├── styles.css
│   └── auth.js
│
├── benchmark.py
├── benchmark_results.txt
├── requirements.txt
├── seed.py
├── README.md
└── taskflow.db
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone <repository-url>
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

---

## Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Backend

```bash
uvicorn backend.main:app --reload
```

Server:

```
http://127.0.0.1:8000
```

---

## Run Frontend

Open

```
frontend/login.html
```

using Live Server.

---

# 📡 API Endpoints

## Authentication

```
POST /auth/register

POST /auth/login

GET /auth/me
```

---

## Tasks

```
GET /tasks

POST /tasks

PUT /tasks/{id}

DELETE /tasks/{id}

GET /tasks/search
```

---

## Projects

```
GET /projects

POST /projects

PUT /projects/{id}

DELETE /projects/{id}
```

---

# 📷 Screenshots

Add screenshots here:

```
login.png

dashboard.png

tasks.png

projects.png
```

---

# 🔮 Future Improvements

- Real AI Integration (OpenAI/Gemini)
- Voice Commands
- Email Notifications
- Calendar Integration
- Team Collaboration
- File Attachments
- Dark / Light Theme
- Drag & Drop Tasks
- Kanban Board
- Analytics Dashboard

---

# 📄 License

This project is developed for educational purposes.

---

# 👨‍💻 Developer

**Manish Kevat**

BCA Student

AI Assisted Task Management Platform

TaskFlow2 – 2026


## ⭐ Key Highlights

- AI Assisted Task Creation
- Offline Rule-Based NLP Parser
- FastAPI REST API
- SQLAlchemy ORM
- JWT Authentication
- MySql Database
- Linear Search
- Binary Search
- Insertion Sort
- Responsive Dashboard
- Local Storage Cache
- Project & Task CRUD