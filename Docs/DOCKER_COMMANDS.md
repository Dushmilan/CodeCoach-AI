# 🐳 Docker Compose Commands Cheat Sheet

Quick reference for managing CodeCoach AI services individually.

---

## 📋 Service Overview

| Service | Port | Purpose |
|---------|------|---------|
| `frontend` | 3000 | Next.js React UI |
| `backend` | 8000 | FastAPI + AI Coaching |
| `piston` | 2000 | Code Execution Engine |

---

## 🎯 Control Individual Services

### Stop/Start/Restart

```bash
# Stop specific services
docker compose stop frontend
docker compose stop backend
docker compose stop piston

# Start specific services
docker compose start frontend
docker compose start backend
docker compose start piston

# Restart specific services
docker compose restart frontend
docker compose restart backend
docker compose restart piston

# Stop multiple services
docker compose stop frontend backend
```

---

## 📜 View Logs

```bash
# All services (combined)
docker compose logs

# All services with follow (real-time)
docker compose logs -f

# Specific service logs
docker compose logs frontend
docker compose logs backend
docker compose logs piston

# Follow specific service (real-time)
docker compose logs -f frontend
docker compose logs -f backend

# Last N lines only
docker compose logs --tail=50 backend
docker compose logs --tail=100 frontend

# With timestamps
docker compose logs -f --timestamps backend
```

### Log Examples

```bash
# Watch backend errors in real-time
docker compose logs -f backend | grep -i error

# Save logs to file
docker compose logs backend > backend-logs.txt

# Check last 20 lines of piston
docker compose logs --tail=20 piston
```

---

## 📦 Install Packages

### Backend (Python)

```bash
# Temporary installation (lost on rebuild)
docker compose exec backend pip install package-name

# Examples
docker compose exec backend pip install pandas
docker compose exec backend pip install numpy
docker compose exec backend pip install requests

# Check installed packages
docker compose exec backend pip list

# Uninstall package
docker compose exec backend pip uninstall package-name
```

### Frontend (Node.js)

```bash
# Temporary installation (lost on rebuild)
docker compose exec frontend npm install package-name
# or
docker compose exec frontend pnpm add package-name

# Examples
docker compose exec frontend npm install lodash
docker compose exec frontend npm install axios
docker compose exec frontend pnpm add react-query

# Check installed packages
docker compose exec frontend npm list

# Uninstall package
docker compose exec frontend npm uninstall package-name
```

### ⚠️ Make Packages Permanent

Packages installed via `exec` are **temporary**. To make them permanent:

**Backend:**
```bash
# 1. Add to backend/requirements.txt
echo "pandas" >> backend/requirements.txt

# 2. Rebuild
docker compose build backend

# 3. Restart
docker compose up -d backend
```

**Frontend:**
```bash
# 1. Add to frontend/package.json
npm install lodash --save

# 2. Rebuild
docker compose build frontend

# 3. Restart
docker compose up -d frontend
```

---

## 💻 Execute Commands Inside Containers

### Open Shell Access

```bash
# Backend shell
docker compose exec backend sh
# or
docker compose exec backend /bin/bash

# Frontend shell
docker compose exec frontend sh
# or
docker compose exec frontend /bin/bash

# Piston shell (if needed)
docker compose exec piston sh
```

### Run One-Off Commands

```bash
# Backend
docker compose exec backend python -c "print('Hello')"
docker compose exec backend python --version
docker compose exec backend env | grep NVIDIA
docker compose exec backend ls -la /app

# Frontend
docker compose exec frontend node -v
docker compose exec frontend npm -v
docker compose exec frontend env | grep API
docker compose exec frontend ls -la /app

# Database operations
docker compose exec backend python -m pytest
docker compose exec backend python manage.py migrate
```

---

## 🔨 Build & Rebuild

```bash
# Build all services
docker compose build

# Build specific service
docker compose build frontend
docker compose build backend
docker compose build piston

# Build without cache
docker compose build --no-cache frontend
docker compose build --no-cache backend

# Build and start
docker compose up --build frontend
docker compose up -d --build backend
```

---

## 🗑️ Remove & Clean

```bash
# Stop and remove specific container
docker compose rm -f frontend
docker compose rm -f backend

# Stop all containers
docker compose down

# Remove containers and volumes (deletes data!)
docker compose down -v

# Remove everything including images
docker compose down -v --rmi all

# Clean up dangling images
docker image prune -f
```

---

## 📊 Check Status & Resources

```bash
# All services status
docker compose ps

# Specific service (filter)
docker compose ps | findstr frontend  # Windows
docker compose ps | grep frontend     # Linux/Mac

# Resource usage (CPU, Memory)
docker stats

# Container details
docker inspect codecoach-backend
docker inspect codecoach-frontend

# Check network
docker network inspect codecoach-network
```

---

## 🚀 Start/Stop All Services

```bash
# Start all (detached mode - background)
docker compose up -d

# Start all (foreground - see logs)
docker compose up

# Stop all
docker compose down

# Stop all and remove volumes
docker compose down -v

# Restart all
docker compose restart

# Rebuild and restart all
docker compose up -d --build
```

---

## 🔍 Practical Debugging Scenarios

### Scenario 1: Backend Not Starting

```bash
# 1. Check logs
docker compose logs backend

# 2. Check if container is running
docker compose ps backend

# 3. Inspect container
docker inspect codecoach-backend

# 4. Check environment variables
docker compose exec backend env | grep NVIDIA

# 5. Test database connection
docker compose exec backend python -c "import sqlite3; print('OK')"
```

### Scenario 2: Frontend Can't Connect to Backend

```bash
# 1. Check frontend env vars
docker compose exec frontend sh -c "env | grep API"

# 2. Check backend is running
docker compose ps backend

# 3. Test backend health from host
curl http://localhost:8000/api/health

# 4. Test from frontend container
docker compose exec frontend wget -qO- http://backend:8000/api/health

# 5. Check network connectivity
docker compose exec frontend ping backend
```

### Scenario 3: Code Execution Failing

```bash
# 1. Check piston logs
docker compose logs -f piston

# 2. Check if piston is running
docker compose ps piston

# 3. Test piston directly
curl http://localhost:2000/api/v2/runtimes

# 4. Check backend can reach piston
docker compose exec backend wget -qO- http://piston:2000/api/v2/runtimes
```

### Scenario 4: Add New Dependency for Testing

```bash
# Backend - temporary test
docker compose exec backend pip install pandas

# Test your code
docker compose exec backend python your_script.py

# If it works, make it permanent
echo "pandas" >> backend/requirements.txt
docker compose build backend
docker compose up -d backend
```

### Scenario 5: View Real-Time Logs of Multiple Services

```bash
# Frontend and backend together
docker compose logs -f frontend backend

# All except piston
docker compose logs -f frontend backend

# With grep for errors
docker compose logs -f backend | grep -i error
```

---

## ⚡ Quick Commands Reference

| Goal | Command |
|------|---------|
| **Stop frontend** | `docker compose stop frontend` |
| **Stop backend** | `docker compose stop backend` |
| **Restart backend** | `docker compose restart backend` |
| **Frontend logs** | `docker compose logs -f frontend` |
| **Backend logs** | `docker compose logs -f backend` |
| **Last 50 lines** | `docker compose logs --tail=50 backend` |
| **Install Python pkg** | `docker compose exec backend pip install <pkg>` |
| **Install Node pkg** | `docker compose exec frontend npm install <pkg>` |
| **Shell into backend** | `docker compose exec backend sh` |
| **Shell into frontend** | `docker compose exec frontend sh` |
| **Rebuild frontend** | `docker compose build frontend` |
| **Rebuild backend** | `docker compose build backend` |
| **Restart single service** | `docker compose up -d --build <service>` |
| **Check status** | `docker compose ps` |
| **Resource usage** | `docker stats` |
| **Remove all** | `docker compose down -v` |

---

## 🎓 Tips & Best Practices

### 1. **Use Detached Mode**
```bash
docker compose up -d  # Runs in background
```

### 2. **Follow Logs in Real-Time**
```bash
docker compose logs -f backend
```

### 3. **Combine Commands**
```bash
# Rebuild and restart backend only
docker compose up -d --build backend
```

### 4. **Check Environment Variables**
```bash
docker compose exec backend env | grep NVIDIA
```

### 5. **Test Service Health**
```bash
# Backend health
curl http://localhost:8000/api/health

# Piston health
curl http://localhost:2000/api/v2/runtimes

# Frontend (check if serving)
curl http://localhost:3000
```

### 6. **Clean Up Orphaned Containers**
```bash
docker compose up -d  # Recreates orphaned containers
```

### 7. **Save Logs for Debugging**
```bash
docker compose logs backend > backend-error.log
```

### 8. **Monitor Resource Usage**
```bash
docker stats  # Real-time CPU/Memory usage
```

---

## 🆘 Troubleshooting Common Issues

### Port Already in Use
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```

### Container Won't Start
```bash
# Check logs
docker compose logs <service>

# Inspect container
docker inspect codecoach-<service>

# Try rebuilding
docker compose build --no-cache <service>
```

### Services Can't Communicate
```bash
# Check they're on same network
docker compose ps

# Test connectivity
docker compose exec frontend ping backend

# Check network
docker network inspect codecoach-network
```

### Out of Disk Space
```bash
# Remove unused data
docker system prune -a

# Remove old images
docker image prune -a

# Remove stopped containers
docker container prune
```

---

## 📚 Additional Resources

- [Docker Compose CLI Reference](https://docs.docker.com/compose/reference/)
- [Docker Exec Command](https://docs.docker.com/engine/reference/commandline/exec/)
- [Docker Logs Command](https://docs.docker.com/engine/reference/commandline/logs/)

---

**Last Updated:** March 20, 2026  
**Project:** CodeCoach AI
