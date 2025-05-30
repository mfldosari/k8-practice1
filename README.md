# 🤖 Chatbot Application (FastAPI + Streamlit)

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red?logo=streamlit)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue?logo=kubernetes)

---

## 📦 Project Structure

```
├── backend.py                # FastAPI backend (REST API)
├── chatbot.py                # Streamlit frontend (UI)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (OpenAI key, etc.)
├── docker/
│   ├── Dockerfile.backend    # Dockerfile for backend
│   ├── Dockerfile.frontend   # Dockerfile for frontend
│   └── docker-compose.yml    # Docker Compose setup
├── Image_gallery/            # Avatars for chat UI
│   ├── bot.png
│   └── user.png
├── chat_logs/                # Local chat history (auto-created)
├── images/                   # Uploaded images (auto-created)
├── k8/
│   ├── backend-deployment.yaml   # Kubernetes deployment for backend
│   ├── backend-service.yaml      # Kubernetes service for backend
│   ├── frontend-deployment.yaml  # Kubernetes deployment for frontend
│   └── frontend-service.yaml     # Kubernetes service for frontend
└── README.md                # This file
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd k8-practice1
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file with your OpenAI API key:
```env
PROJ-OPENAI-API-KEY=sk-...
```

### 3. Run with Docker Compose
```bash
docker-compose up --build
```
- Backend: http://localhost:5000
- Frontend: http://localhost:8501

### 4. Run Locally (Dev)
- Backend:
  ```bash
  uvicorn backend:app --reload --port 5000
  ```
- Frontend:
  ```bash
  streamlit run chatbot.py
  ```

---

## 🐳 Docker & Kubernetes

- **Docker Compose**: Orchestrates backend and frontend with shared volumes for chat logs and images.
- **Kubernetes**: Use the manifests in `k8/` to deploy on any K8s cluster. Update image names as needed.

---

## ✨ Features
- Chat with OpenAI (text and image support)
- Upload images and get AI-powered answers
- Persistent chat history (local JSON)
- Modern UI with avatars
- Ready for Docker & Kubernetes

---

## 📸 Screenshots

| Chat UI | Image Upload |
|---------|-------------|
| ![Chat UI](https://img.icons8.com/color/48/000000/chat--v3.png) | ![Image Upload](https://img.icons8.com/color/48/000000/upload.png) |

---

## 🛠️ Tech Stack
- Python 3.12
- FastAPI
- Streamlit
- Docker & Docker Compose
- Kubernetes (YAML manifests)

---

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License
MIT

---

> Made with ❤️ for AI chat experiments.