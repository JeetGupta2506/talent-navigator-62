# Deployment Guide - Vercel + Render

This guide will help you deploy the Talent Navigator application with:
- **Frontend**: Vercel (React + Vite)
- **Backend**: Render (FastAPI + Python)

---

## 📋 Prerequisites

- GitHub account
- Vercel account (sign up at https://vercel.com)
- Render account (sign up at https://render.com)
- Google API Key for Gemini

---

## 🚀 Part 1: Deploy Backend to Render

### Step 1: Push Your Code to GitHub

```powershell
git add .
git commit -m "Add deployment configurations"
git push origin main
```

### Step 2: Create Render Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `JeetGupta2506/talent-navigator-62`
4. Configure the service:

   **Basic Settings:**
   - **Name**: `talent-navigator-api`
   - **Region**: Choose closest to your users (e.g., Oregon)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

   **Plan:**
   - Select **Free** (or upgrade for better performance)

### Step 3: Add Environment Variables on Render

In the Render dashboard, go to **Environment** tab and add:

```
GOOGLE_API_KEY=your_actual_google_api_key_here
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment to complete (3-5 minutes)
3. Copy your backend URL: `https://talent-navigator-api.onrender.com`

⚠️ **Note**: Free tier may spin down after inactivity (cold starts ~30 seconds)

---

## 🌐 Part 2: Deploy Frontend to Vercel

### Step 1: Create Environment Variable File

Create `.env.production` in the root directory:

```env
VITE_API_URL=https://your-backend-url.onrender.com
```

Replace with your actual Render backend URL.

### Step 2: Commit Environment Config

```powershell
git add .env.production
git commit -m "Add production environment config"
git push origin main
```

### Step 3: Deploy to Vercel

#### Option A: Using Vercel CLI (Recommended)

```powershell
# Install Vercel CLI globally
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

#### Option B: Using Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click **"Add New Project"**
3. Import your GitHub repository: `JeetGupta2506/talent-navigator-62`
4. Configure project:

   **Framework Preset**: Vite
   **Root Directory**: `./` (leave blank)
   **Build Command**: `npm run build`
   **Output Directory**: `dist`

5. Add Environment Variable:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://your-backend-url.onrender.com`

6. Click **"Deploy"**

### Step 4: Verify Deployment

1. Visit your Vercel URL (e.g., `https://talent-navigator-62.vercel.app`)
2. Test the workflow:
   - Upload Job Description
   - Upload Resume
   - Conduct Interview
   - View Results

---

## 🔧 Configuration Files Created

### `vercel.json` (Frontend)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### `backend/render.yaml` (Backend)
```yaml
services:
  - type: web
    name: talent-navigator-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

---

## 🔐 Environment Variables Summary

### Frontend (Vercel)
| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_URL` | `https://your-backend.onrender.com` | Backend API endpoint |

### Backend (Render)
| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_API_KEY` | Your Google API key | Required for Gemini AI |

---

## 🐛 Troubleshooting

### Backend Issues

**Problem**: "Application failed to respond"
- **Solution**: Check Render logs, ensure `PORT` environment variable is used
- Verify `requirements.txt` has all dependencies

**Problem**: "GOOGLE_API_KEY not set"
- **Solution**: Add environment variable in Render dashboard → Environment tab

**Problem**: Cold starts (30+ seconds)
- **Solution**: Upgrade to paid plan or use a keep-alive service (e.g., cron-job.org)

### Frontend Issues

**Problem**: "Failed to fetch" errors
- **Solution**: Verify `VITE_API_URL` is set correctly in Vercel
- Check CORS settings in `backend/main.py`

**Problem**: 404 errors on page refresh
- **Solution**: Ensure `vercel.json` has the rewrite rule for SPA routing

**Problem**: Environment variable not updating
- **Solution**: Redeploy after changing env vars in Vercel dashboard

---

## 🚀 CORS Configuration

Ensure your backend allows requests from your Vercel domain. Check `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://talent-navigator-62.vercel.app",  # Add your Vercel domain
        "https://*.vercel.app",  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring

### Render Dashboard
- View logs: https://dashboard.render.com → Your Service → Logs
- Monitor metrics: CPU, Memory, Requests

### Vercel Dashboard
- View deployments: https://vercel.com/dashboard
- Check analytics: Usage, Performance

---

## 💰 Cost Considerations

### Free Tier Limits

**Render Free:**
- 750 hours/month
- Spins down after 15 minutes of inactivity
- 512 MB RAM
- Shared CPU

**Vercel Free (Hobby):**
- 100 GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS
- Global CDN

### Recommended Upgrades

For production use:
- **Render**: Starter plan ($7/month) - No cold starts, 0.5 CPU, 512 MB RAM
- **Vercel**: Pro plan ($20/month) - Higher limits, team features

---

## 🎉 Success!

Your application should now be live:
- **Frontend**: `https://talent-navigator-62.vercel.app`
- **Backend**: `https://talent-navigator-api.onrender.com`

Test the complete flow:
1. Upload Job Description ✅
2. Upload Resume ✅
3. Conduct Interview ✅
4. View Final Evaluation ✅

---

## 📝 Next Steps

1. **Custom Domain**: Add custom domain in Vercel settings
2. **API Monitoring**: Set up uptime monitoring (e.g., UptimeRobot)
3. **Error Tracking**: Add Sentry or similar service
4. **Analytics**: Add Google Analytics or Plausible
5. **API Rate Limiting**: Implement rate limiting for production

---

## 🔗 Useful Links

- Vercel Documentation: https://vercel.com/docs
- Render Documentation: https://render.com/docs
- GitHub Repository: https://github.com/JeetGupta2506/talent-navigator-62
