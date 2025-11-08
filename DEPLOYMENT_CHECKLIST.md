# 🚀 Quick Deployment Checklist

## Pre-Deployment

- [ ] All code committed and pushed to GitHub
- [ ] `.env` file not committed (check with `git ls-files | Select-String "\.env"`)
- [ ] Backend tested locally (`cd backend; uvicorn main:app --reload`)
- [ ] Frontend tested locally (`npm run dev`)
- [ ] Google API Key ready

## Backend Deployment (Render)

- [ ] Create new Web Service on Render
- [ ] Connect GitHub repository
- [ ] Set Root Directory: `backend`
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Add Environment Variable: `GOOGLE_API_KEY`
- [ ] Wait for deployment (3-5 minutes)
- [ ] Copy backend URL (e.g., `https://talent-navigator-api.onrender.com`)
- [ ] Test health endpoint: `https://your-backend-url.onrender.com/health`

## Frontend Deployment (Vercel)

- [ ] Update `.env.production` with backend URL
- [ ] Commit and push changes
- [ ] Create new project on Vercel
- [ ] Import GitHub repository
- [ ] Add Environment Variable: `VITE_API_URL=https://your-backend-url.onrender.com`
- [ ] Deploy
- [ ] Wait for deployment (1-2 minutes)
- [ ] Visit your Vercel URL

## Post-Deployment Testing

- [ ] Frontend loads without errors
- [ ] Upload Job Description works
- [ ] Upload Resume works
- [ ] Resume screening shows scores
- [ ] Interview generation works
- [ ] Interview scoring works
- [ ] Final evaluation displays correctly
- [ ] Check browser console for errors
- [ ] Test on mobile device

## Optional Enhancements

- [ ] Add custom domain on Vercel
- [ ] Set up monitoring (UptimeRobot)
- [ ] Enable error tracking (Sentry)
- [ ] Add analytics (Google Analytics)
- [ ] Configure rate limiting

## Troubleshooting

### If backend doesn't start:
1. Check Render logs
2. Verify `GOOGLE_API_KEY` is set
3. Check `requirements.txt` includes all dependencies

### If frontend can't connect to backend:
1. Verify `VITE_API_URL` environment variable
2. Check CORS settings in backend
3. Test backend URL directly in browser

### If you see cold start delays:
- This is normal for Render free tier (spins down after 15 min)
- First request may take 30+ seconds
- Consider upgrading to paid plan

## Commands Quick Reference

```powershell
# Push code
git add .
git commit -m "Deploy configuration"
git push origin main

# Install Vercel CLI
npm install -g vercel

# Deploy to Vercel
vercel --prod

# Test backend locally
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test frontend locally
npm run dev

# Build frontend
npm run build
```

## Support

- Vercel: https://vercel.com/docs
- Render: https://render.com/docs
- Full Guide: See DEPLOYMENT.md
