# Dream Journal - Claude Code Memory

## Project Overview
A dream journal web application built with Django (backend) and Quasar/Vue (frontend).

## Tech Stack
- **Backend**: Django 5.2.5 LTS + Django REST Framework 3.16.1
- **Frontend**: Quasar 2 + Vue 3 + TypeScript
- **Database**: PostgreSQL 16 (containerized)
- **Python**: 3.13.7 (managed via pyenv)
- **Node**: 22.18.0 LTS (managed via fnm)

## Architectural Principles

### Framework-First Approach
**ALWAYS search for solutions within the chosen frameworks first, before implementing custom solutions.**

1. **Quasar/Vue Frontend**:
   - Use Quasar components and utilities (e.g., `q-pa-md`, `col-*`, `q-btn`)
   - Follow Vue Composition API patterns with `<script setup>`
   - Use Vue Router for navigation and auth guards
   - Leverage Pinia for state management
   - Avoid custom CSS when Quasar utilities exist

2. **Django/DRF Backend**:
   - Use Django's built-in features (auth, middleware, settings)
   - Follow DRF patterns for API design
   - Use django-extensions and established packages over custom code
   - Leverage Django's ORM and admin interface

3. **Authentication & Security Pattern**:
   - **JWT Authentication**: Pure JWT-based API authentication (no sessions)
   - **Token Storage**: localStorage for JWT tokens (access + refresh)
   - **No CSRF Protection**: Not needed for JWT Bearer token auth via headers
   - **Single source**: Router guards handle auth state and navigation
   - **Token refresh**: Axios interceptors handle token mechanics only
   - **State management**: Pinia store for clean auth state
   - **Security focus**: XSS prevention via CSP headers, not CSRF protection

### Decision Hierarchy
When solving problems, check solutions in this order:
1. **Framework built-ins** (Quasar components, Django features)
2. **Official plugins/packages** (Vue Router, DRF extensions)
3. **Established ecosystem libraries** (Axios, Pinia plugins)
4. **Custom implementation** (only if no framework solution exists)

### Anti-Patterns to Avoid
- ❌ **Multiple competing solutions** (e.g., custom CSS + Quasar utilities)
- ❌ **Mixed responsibility patterns** (e.g., auth logic in multiple places)
- ❌ **Framework bypassing** (e.g., custom responsive breakpoints when Quasar has them)
- ❌ **Configuration duplication** (e.g., hardcoding URLs in multiple files)

## Project Structure
```
dream-journal/
├── backend/                 # Django backend
│   ├── venv/               # Python virtual environment
│   ├── dream_journal/      # Django project settings
│   ├── manage.py
│   ├── requirements.txt
│   ├── pyproject.toml      # Ruff configuration
│   ├── mypy.ini           # MyPy type checking config
│   └── .env.local         # Environment variables
├── frontend/               # Quasar/Vue frontend
│   ├── src/               # Source code
│   ├── package.json
│   ├── quasar.config.ts
│   └── tsconfig.json
├── localdev/              # Development services
│   └── docker-compose.yml # PostgreSQL container
├── .python-version        # Python version (3.13.7)
├── .node-version         # Node version (22.18.0)
└── .gitignore
```

## Development Setup

### Prerequisites
- pyenv (Python version management)
- fnm (Node version management)
- Docker (for PostgreSQL)

### Environment Setup
```bash
# Python/Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Node/Frontend
cd frontend
export PATH="/home/kjs/.local/share/fnm:$PATH" && eval "$(fnm env)"
npm install
```

### Database Setup
```bash
# Start PostgreSQL container
cd localdev && docker compose up -d

# Run migrations
cd ../backend && source venv/bin/activate
python manage.py migrate
```

### Running the Applications
```bash
# Backend (Terminal 1)
cd backend && source venv/bin/activate
python manage.py runserver > server.log 2>&1

# Frontend (Terminal 2)  
cd frontend && export PATH="/home/kjs/.local/share/fnm:$PATH" && eval "$(fnm env)"
npm run dev > server.log 2>&1
```

### Server Logs
- **Backend logs**: `backend/server.log` - Django development server output
- **Frontend logs**: `frontend/server.log` - Quasar development server output
- **Note**: Log files are already in .gitignore (*.log pattern)

## URLs
- **Backend API**: http://localhost:8081
- **Django Admin**: http://localhost:8081/admin (admin/admin)
- **Frontend**: http://localhost:9000
- **PostgreSQL**: localhost:5431 (dreamjournal/dreamjournal/dreamjournal)

## Configuration Details

### Backend (.env.local)
```
SECRET_KEY=89@6j-ceuuvtsi=zq#kyl5(eh_4tev(j^!jna&o^)v408ic1t5
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://dreamjournal:dreamjournal@localhost:5431/dreamjournal
CORS_ALLOWED_ORIGINS=http://localhost:9000
```

### Code Quality Tools
- **Ruff**: Python linting + formatting (strict type hints, no Any allowed)
- **MyPy**: Static type checking with strict settings
- **ESLint**: JavaScript/TypeScript linting with strict rules
- **Prettier**: Code formatting

### Code Standards & Style Guide

#### TypeScript/Vue Rules
- **Always use explicit type annotations** - Functions must have return types
- **No floating promises** - Use `void` operator for fire-and-forget promises: `void router.push('/')`
- **No `any` types** - Use proper TypeScript types or `unknown`
- **No `require()` imports** - Use ES6 `import` or dynamic `import()` for code splitting
- **Handle all promise rejections** - Either await, catch, or mark with `void`
- **Remove unused variables** - Use `_` prefix or omit parameter names in catch blocks
- **Prefer dynamic imports** - Use `await import()` over `require()` for conditional imports

#### Python Rules
- **Mandatory type hints** - All functions, parameters, and return values must be typed
- **No `Any` type** - Enforced by Ruff configuration
- **Strict MyPy checking** - All type errors must be resolved
- **Format with Ruff** - Consistent code formatting

#### Example Patterns
```typescript
// ✅ Good - Explicit void for floating promise
void router.push('/')

// ✅ Good - Proper async/await
const result = await authStore.login(credentials)

// ✅ Good - Dynamic import for code splitting
const { useAuthStore } = await import('stores/auth')

// ✅ Good - Unused parameter handling
} catch {
  console.warn('Request failed')
}

// ❌ Bad - Floating promise
router.push('/')

// ❌ Bad - require() import
const { useAuthStore } = require('stores/auth')
```

### Key Django Settings
- REST Framework with session authentication
- CORS configured for frontend origin
- PostgreSQL database via dj-database-url
- Environment variables via python-dotenv

### Frontend Configuration
- Quasar CLI with Vite
- TypeScript enabled
- Pinia for state management
- Axios for API calls
- Proxy configured: `/api` → `http://localhost:8000`

## Development Commands

### Backend
```bash
# Run server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Type checking
mypy .

# Linting
ruff check .

# Format code
ruff format .
```

### Frontend
```bash
# Development server
npm run dev

# Build for production
npm run build

# Lint code (must pass before committing)
npm run lint

# Format code
npm run format

# Type check
npx vue-tsc --noEmit
```

### Database
```bash
# Start services
cd localdev && docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs postgres
```

## Security Architecture

### Authentication Flow
1. **Login**: User credentials → JWT tokens (access + refresh) stored in localStorage
2. **API Requests**: Authorization header with Bearer token for all API calls
3. **Token Refresh**: Automatic refresh via axios interceptors when access token expires
4. **Logout**: Clear tokens from localStorage and redirect to login

### Why No CSRF Protection
- **JWT tokens in localStorage**: Not sent automatically with requests (unlike cookies)
- **Authorization headers**: Must be set explicitly by JavaScript (CSRF can't do this)
- **Stateless authentication**: No session cookies that could be exploited via CSRF
- **Admin interface**: Django's built-in CSRF handles admin pages automatically

### Security Measures
- **HTTPS in production**: Prevents token interception
- **Short-lived access tokens**: 1 hour expiration with automatic refresh
- **Token rotation**: New refresh tokens on each refresh (prevents replay attacks)
- **CORS configuration**: Restricts cross-origin requests to allowed origins

## Notes
- Frontend automatically proxies `/api` requests to Django backend
- PostgreSQL runs in Docker on port 5431 to avoid conflicts
- Type hints are mandatory in Python code (enforced by Ruff + MyPy)
- Admin user: admin/admin for development