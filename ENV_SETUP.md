# Environment Variables Setup

## Local Development

### Backend (.env in backend/)
```env
GOOGLE_API_KEY=your_google_api_key_here
```

### Frontend (.env.local in root)
```env
VITE_API_URL=http://localhost:8000
```

## Production Deployment

### Backend (Render)
Add these in Render Dashboard → Environment tab:
```
GOOGLE_API_KEY=your_google_api_key_here
```

### Frontend (Vercel)
Add these in Vercel Dashboard → Settings → Environment Variables:
```
VITE_API_URL=https://your-backend-name.onrender.com
```

## Getting Google API Key

1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Add it to your environment variables

⚠️ **Security Note**: Never commit API keys to git!

## Files Overview

- `.env` - Backend local development (gitignored)
- `.env.local` - Frontend local development (gitignored)
- `.env.production` - Frontend production config (can be committed with placeholder)
- `.env.example` - Template file (safe to commit)
