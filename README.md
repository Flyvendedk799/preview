# Preview SaaS Dashboard

A modern, premium SaaS dashboard for automatically generating branded URL previews for websites.

> Database migrations applied - columns fixed and up to date.

## Tech Stack

- **React** + **Vite** - Fast development and build tooling
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Heroicons** - Beautiful SVG icons
- **Inter Font** - Clean, modern typography

## Project Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Layout.tsx      # Main layout wrapper
│   │   ├── Sidebar.tsx      # Navigation sidebar
│   │   └── Header.tsx       # Top header bar
│   └── ui/
│       ├── Card.tsx         # Reusable card component
│       ├── Button.tsx       # Button component
│       └── Modal.tsx        # Modal dialog component
├── pages/
│   ├── Dashboard.tsx        # Dashboard home page
│   ├── Domains.tsx         # Domain management page
│   ├── Brand.tsx           # Brand settings page
│   ├── Previews.tsx        # Preview gallery page
│   ├── Analytics.tsx       # Analytics page
│   └── Billing.tsx         # Billing page
├── router/
│   └── Router.tsx          # Route configuration
├── App.tsx                 # Main app component
├── main.tsx                # Entry point
└── index.css               # Global styles
```

## Design Principles

- Clean, minimal, premium aesthetic
- Generous whitespace
- Strong typography hierarchy
- Rounded corners (8px)
- Soft, subtle shadows
- Smooth hover states
- Simple, focused UIs

## Color Palette

- **Primary**: #2979FF (Blue)
- **Secondary**: #0A1A3C (Dark Navy)
- **Accent**: #3FFFD3 (Cyan)
- **Background**: #F5F7FA (Light Gray)
- **Neutrals**: Soft gray scale for text and borders

## Setup Instructions

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

4. **Preview production build:**
   ```bash
   npm run preview
   ```

## Features

- ✅ Responsive sidebar navigation
- ✅ Mobile-friendly mobile menu
- ✅ Dashboard with stat cards
- ✅ Domain management table
- ✅ Brand settings with preview
- ✅ Preview gallery with filters
- ✅ Analytics dashboard
- ✅ Billing and subscription management

## Backend Integration

The frontend is now connected to a FastAPI backend running at `http://localhost:8000` by default.

### Backend Setup

See `backend/README_backend.md` for detailed backend setup instructions.

### Production Deployment

For production deployment on Railway, see [DEPLOYMENT.md](./DEPLOYMENT.md).

### Environment Variables

For a complete list of environment variables, see [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md).

**Quick Start:**

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # macOS/Linux
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Run the backend server:**
   ```bash
   uvicorn backend.main:app --reload
   ```

### Frontend Configuration

The frontend reads the API base URL from environment variables:

- Create a `.env` file (or copy `.env.example`) with:
  ```
  VITE_API_BASE_URL=http://localhost:8000
  ```

- If not set, defaults to `http://localhost:8000`

### Running Both Services

**Terminal 1 - Backend:**
```bash
uvicorn backend.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

The frontend will automatically connect to the backend API. CORS is configured to allow requests from the Vite dev server.

## Authentication

The application uses JWT-based authentication:

- **Backend**: JWT tokens issued via `/api/v1/auth/login` and `/api/v1/auth/signup`
- **Frontend**: Token stored in localStorage, all `/app/*` routes are protected
- **Protected Routes**: All dashboard routes require authentication

### Testing Authentication

1. **Start backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```

2. **Start frontend:**
   ```bash
   npm run dev
   ```

3. **Create an account:**
   - Navigate to `/signup`
   - Enter email and password
   - Account is created and you're automatically logged in

4. **Login:**
   - Navigate to `/login`
   - Enter your credentials
   - You'll be redirected to `/app` dashboard

5. **Access protected routes:**
   - All `/app/*` routes require authentication
   - If not logged in, you'll be redirected to `/login`
   - Token is automatically included in API requests

6. **Logout:**
   - Click on your email in the header
   - Select "Logout" from the dropdown menu

## Development

- **Phase 1-2**: Frontend foundation with mock data
- **Phase 3**: FastAPI backend with in-memory storage
- **Phase 4**: Frontend-backend integration
- **Phase 5**: SQLAlchemy database integration
- **Phase 6**: JWT authentication system (current)

## Troubleshooting

### Frontend Can't Connect to Backend (ERR_CONNECTION_REFUSED)

**Symptoms:**
- Browser console shows `ERR_CONNECTION_REFUSED` when making API calls
- Signup/login fails with "Failed to fetch"
- Frontend is trying to connect to `localhost:8000` instead of Railway backend

**Solution:**
1. **Check Environment Variables**: Ensure `VITE_API_BASE_URL` is set in your Railway frontend service
   - Go to Railway dashboard → Your frontend service → Variables
   - Add: `VITE_API_BASE_URL=https://your-backend-service.railway.app/api/v1`
   - **Important**: Include `/api/v1` in the URL

2. **Rebuild Frontend**: After setting the variable, Railway will automatically rebuild
   - Check build logs to confirm the variable is being used
   - Look for `[App Startup] API Base URL:` in browser console

3. **Verify Backend is Running**: 
   - Check Railway backend service logs
   - Look for startup message: `Starting Preview SaaS API`
   - Test backend health: `curl https://your-backend-service.railway.app/health`

4. **Check CORS Settings**:
   - Ensure `CORS_ALLOWED_ORIGINS` in backend includes your frontend URL
   - Format: `https://your-frontend.railway.app` (comma-separated if multiple)

### Backend Not Starting

**Check Logs:**
- Railway logs will show startup errors
- Look for database connection errors
- Verify all required environment variables are set

**Common Issues:**
- Missing `DATABASE_URL` → Backend can't connect to PostgreSQL
- Missing `SECRET_KEY` → JWT signing fails
- Missing `REDIS_URL` → Job queue won't work
- Missing `OPENAI_API_KEY` → AI preview generation fails

### Debugging Tips

1. **Frontend Console Logs**: Open browser DevTools → Console
   - Look for `[App Startup]` messages showing API URL
   - Check for `[API]` logs showing request URLs
   - Check for `[API Error]` logs showing connection failures

2. **Backend Logs**: Check Railway backend service logs
   - Startup logs show environment and configuration
   - Request logs show all API calls with request IDs
   - Error logs show detailed stack traces

3. **Health Check**: Test backend health endpoint
   ```bash
   curl https://your-backend-service.railway.app/health
   ```
   Should return: `{"status": "ok", "version": "1.0.0"}`

