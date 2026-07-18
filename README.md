# PyQuest: AI-Powered Python Learning Platform using LLM-Assisted Intelligent Agents

PyQuest is an AI-powered game-based Python learning platform that combines **Large Language Models (LLMs)**, a **4-Agent intelligent architecture**, **gamification**, and **adaptive learning** to provide an engaging programming education experience.

The platform leverages **Groq's Llama-3.1-8B-Instant** model through four specialized AI agents responsible for **question generation, secure code execution, solution verification, and contextual hint generation**. It dynamically generates Python coding puzzles, evaluates user solutions, provides intelligent feedback, and supports multiple learning modes for skill development and coding interview preparation.

---

# Features

- AI-powered Python puzzle generation
- LLM-assisted intelligent agent workflow
- Secure sandboxed Python code execution
- Semantic solution verification using LLM
- Context-aware hint generation
- Adaptive learning based on user performance
- Multiple interactive game modes
- Python interview preparation
- User authentication and progress tracking
- Persistent scoring and statistics

---

# Core Technologies

## Programming Language
- Python 3.10

## Backend
- Flask
- Flask-SQLAlchemy
- SQLAlchemy ORM

## Frontend
- HTML5
- CSS3
- Vanilla JavaScript

## Database
- SQLite

## Artificial Intelligence
- Large Language Models (LLMs)
- Groq API
- Llama-3.1-8B-Instant

## Secure Code Execution
- Python subprocess
- Sandboxed execution
- Timeout protection

---

# AI Agent Architecture

PyQuest follows a **4-Agent intelligent workflow** where each agent performs a dedicated task to improve the learning experience.

| Agent | Responsibility |
|--------|----------------|
| **Agent 1 – Question Generator** | Generates Python coding puzzles using the Groq LLM based on the selected topic and difficulty level. Validates generated questions before presenting them to learners. |
| **Agent 2 – Sandbox Executor** | Executes user-submitted Python code inside a secure sandbox environment while restricting unsafe operations and capturing execution results. |
| **Agent 3 – Solution Verifier** | Compares program output with the expected solution and uses the LLM to recognize semantically correct alternative implementations. |
| **Agent 4 – Hint Generator** | Produces contextual hints that guide learners toward the solution without revealing the complete answer. |

---

# Learning Modes

### Classic Mode
- Fill-in-the-blank Python coding puzzles
- Multiple attempts with score-based evaluation

### Adaptive Mode
- Dynamic difficulty adjustment
- Personalized learning based on user performance

### Drag & Fill Mode
- Interactive drag-and-drop code completion
- Improves syntax recognition and logical thinking

### Interview Mode
- Complete Python programming problems
- AI-assisted evaluation of correctness and algorithm complexity

---

# Project Structure

```
PyQuest/
│
├── database/
├── models/
├── routes/
├── services/
├── templates/
├── utils/
│
├── app.py
├── config.py
├── migrate_db.py
├── reset_db.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

# Installation

## Clone the Repository

```bash
git clone https://github.com/rashid-np/pyquest-ai-learning.git
cd pyquest-ai-learning
```

## Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

Create a `.env` file in the project directory.

Example:

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY
SECRET_KEY=YOUR_SECRET_KEY
```

## Run the Application

```bash
python app.py
```

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

# Demo/Screenshots


```
screenshots/
│
├── login.png
├── home.png
├── classic_mode.png
├── adaptive_mode.png
├── drag_fill.png
├── interview_mode.png
└── dashboard.png
```

---

# Key Functionalities

- User Authentication
- AI-Based Question Generation
- Secure Python Code Execution
- LLM-Assisted Solution Verification
- Intelligent Hint Generation
- Adaptive Learning
- Interview Preparation
- Progress Tracking
- Performance Analytics

---

# Future Enhancements

- Public Leaderboard
- Monaco Editor Integration
- Test Case Based Evaluation
- Instructor Dashboard
- Mobile Application
- Multi-language Programming Support
- Personalized Learning Analytics

---

# Applications

- Python Programming Education
- Coding Bootcamps
- Online Learning Platforms
- Coding Interview Preparation
- Academic Institutions
- Self-paced Learning

---

# License

This project is licensed under the **MIT License**.

---

# Author

**Rashid N**

MCA Graduate

**Interests:** Artificial Intelligence • Machine Learning • Computer Vision

**GitHub:** https://github.com/rashid-np

**LinkedIn:** https://www.linkedin.com/in/rashid-n-4509bb335

---

# Acknowledgements

- Groq
- Meta Llama
- Flask
- SQLAlchemy
- Python Software Foundation
- Open Source Community
