# 🚀 CodeCoach AI - Deployment Guide

## Quick Deploy Options

### Option 1: Oracle Cloud Free Tier (Recommended for 24/7 Demo)

**What you get:**
- ✅ 4 ARM cores + 24GB RAM (always free)
- ✅ Runs all services: Frontend + Backend + Piston + Redis
- ✅ No spin-down, permanent demo
- ✅ Free public IP address

**Steps:**

1. **Sign up for Oracle Cloud Free Tier:**
   - Visit: https://www.oracle.com/cloud/free/
   - Create account (requires credit card for verification, no charges)

2. **Create VM Instance:**
   - Go to Compute → Instances
   - Create Instance
   - Image: Ubuntu 22.04
   - Shape: VM.Standard.A1.Flex (4 OCPU, 24GB RAM)
   - SSH key: Generate or upload your key

3. **Connect to VM:**
   ```bash
   ssh -i your_key.pem ubuntu@your-vm-ip
   ```

4. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   ```

5. **Clone and Deploy:**
   ```bash
   git clone https://github.com/your-username/CodeCoach-AI.git
   cd CodeCoach-AI
   cp .env.example .env
   # Edit .env with your NVIDIA API key
   nano .env
   # Deploy
   docker compose up -d --build
   ```

6. **Access Your Demo:**
   - Frontend: `http://your-vm-ip:3000`
   - Backend API: `http://your-vm-ip:8000`
   - API Docs: `http://your-vm-ip:8000/docs`

---

### Option 2: Google Cloud Run (Pay-as-you-go, Free Tier)

**What you get:**
- ✅ 2 million requests/month free
- ✅ Auto-scales to zero (no cost when idle)
- ⚠️ Cold start delay (~5s) after inactivity

**Steps:**

1. **Create Google Cloud Account:**
   - Visit: https://cloud.google.com/free
   - $300 free credit for 90 days

2. **Enable Cloud Run API:**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

3. **Deploy Backend:**
   ```bash
   cd backend
   gcloud run deploy codecoach-backend \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars NVIDIA_API_KEY=your_key
   ```

4. **Deploy Frontend:**
   ```bash
   cd frontend
   gcloud run deploy codecoach-frontend \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars NEXT_PUBLIC_API_URL=https://your-backend-url.a.run.app
   ```

---

### Option 3: Hugging Face Spaces (100% Free, No Credit Card)

**What you get:**
- ✅ 3 free Docker Spaces (16GB storage each)
- ✅ No credit card required
- ⚠️ Spaces spin down after 48h inactivity

**Steps:**

1. **Create Hugging Face Account:**
   - Visit: https://huggingface.co/join

2. **Create Backend Space:**
   - New Space → Docker
   - Upload `backend/` folder
   - Add `Dockerfile` (already included)
   - Set environment variable: `NVIDIA_API_KEY`

3. **Create Frontend Space:**
   - New Space → Docker
   - Upload `frontend/` folder
   - Add `Dockerfile` (already included)
   - Set environment: `NEXT_PUBLIC_API_URL=https://your-backend.hf.space`

4. **Access:**
   - Frontend: `https://huggingface.co/spaces/your-username/codecoach-frontend`
   - Backend: `https://huggingface.co/spaces/your-username/codecoach-backend`

---

### Option 4: Vercel + Hugging Face (Best Performance)

**Frontend on Vercel:**
- ✅ Automatic Next.js optimization
- ✅ Global CDN
- ✅ Free HTTPS

**Backend on Hugging Face:**
- ✅ Free Docker container hosting

**Steps:**

1. **Deploy Backend to Hugging Face** (see Option 3)

2. **Deploy Frontend to Vercel:**
   ```bash
   cd frontend
   npx vercel
   # Set environment variables in Vercel dashboard:
   # NEXT_PUBLIC_API_URL=https://your-backend.hf.space
   ```

---

## Local Testing with Docker Compose

Before deploying, test locally:

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env with your NVIDIA API key
nano .env  # or use your preferred editor

# 3. Start all services (3 services: frontend, backend, piston)
docker compose up --build

# 4. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Piston: http://localhost:2000

# 5. Stop services
docker compose down
```

**Note:** Rate limiting uses in-memory storage (SlowAPI), no Redis needed.

---

## Architecture

```
┌─────────────┐
│  Frontend   │  Port 3000 (Next.js)
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Backend   │────►│   Piston     │  Code execution
│  (FastAPI)  │     │  (Sandbox)   │
└──────┬──────┘     └──────────────┘
       │
       └──► SQLite (embedded, no extra service)
```

**Services:**
- **Frontend** (port 3000): Next.js React app
- **Backend** (port 8000): FastAPI with SlowAPI rate limiting (in-memory)
- **Piston** (port 2000): Code execution engine
- **No Redis needed**: Rate limiting uses in-memory storage

| Variable | Description | Required |
|----------|-------------|----------|
| `NVIDIA_API_KEY` | NVIDIA NIM API key for AI coaching | ✅ Yes |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | ✅ Yes |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL for real-time features | ✅ Yes |

**Get your free NVIDIA API key:** https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct

---

## Cost Comparison

| Platform | Frontend | Backend | Piston | Total/Month |
|----------|----------|---------|--------|-------------|
| **Oracle Cloud** | Free | Free | Free | **$0** |
| **Google Cloud Run** | ~$0* | ~$0* | ~$0* | **~$0** (2M req free) |
| **Hugging Face** | Free | Free | Free | **$0** |
| **Vercel + HF** | Free | Free | Free | **$0** |
| **Render** | Free | Free | Free | **$0** (with limitations) |
| **Netlify** | ✅ Frontend only | ❌ Not supported | ❌ | **N/A** |

*Within free tier limits

**Note:** Only 3 Docker containers needed (no Redis/database overhead).

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

### Docker Compose Issues
```bash
# Clean rebuild
docker compose down -v
docker compose up --build --force-recreate
```

### Backend Can't Connect to Piston
- Ensure all services are on the same Docker network
- Check Piston health: `http://localhost:2000/api/v2/runtimes`

### Frontend Shows Blank Page
- Check browser console for errors
- Verify `NEXT_PUBLIC_API_URL` is correct
- Rebuild frontend: `docker compose build frontend`

---

## Security Notes for Production

⚠️ **Before going public:**

1. **Add Authentication:** Protect your demo with basic auth or OAuth
2. **Rate Limiting:** Already implemented in backend (adjust limits in `app/middleware/`)
3. **HTTPS:** Use a reverse proxy (Nginx) or Cloudflare for SSL
4. **API Key Security:** Never commit `.env` files to Git
5. **Database Backup:** Regular backups of SQLite database

---

## Need Help?

- Oracle Cloud Setup: https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/launchinginstance.htm
- Docker Compose Docs: https://docs.docker.com/compose/
- NVIDIA NIM API: https://docs.nvidia.com/nim/
