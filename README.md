
# Flask-SQLAlchemy Backend Setup Guide

## Updated Folder Structure (with services)

```
backend/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── discover.py
│   ├── carbon.py
│   ├── dashboard.py
│   └── activity.py
│
├── routes/
│   ├── __init__.py
│   ├── user_routes.py
│   ├── discover_routes.py
│   ├── carbon_routes.py
│   ├── dashboard_routes.py
│   └── activity_routes.py
│
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   ├── discover_service.py
│   ├── carbon_service.py
│   ├── dashboard_service.py
│   └── activity_service.py
└── tests/
    ├── __init__.py
    ├── test_user.py
    └── conftest.py
```

## Initialization Steps

### 1. Create Project Directory
```bash
mkdir backend
cd backend
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Initialize Git
```bash
git init
git checkout -b dev
```

### 4. Create All Directories
```bash
mkdir models routes services utils tests
touch models/__init__.py routes/__init__.py services/__init__.py utils/__init__.py tests/__init__.py
```

### 5. Install Dependencies
```bash
pip install flask flask-sqlalchemy flask-migrate flask-cors python-dotenv flask-jwt-extended
pip freeze > requirements.txt
```

### 6. Set Up Environment Variables
Create `.env` file (keep this secret):
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
JWT_SECRET_KEY=your-jwt-secret-key
```

Create `.env.example` (commit this):
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=
DATABASE_URL=
JWT_SECRET_KEY=
```

### 7. Initialize Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 8. Run the Application
```bash
flask run
```

## Git Workflow

### Initial Commit
```bash
git add .
git commit -m "Initial Flask backend setup with folder structure"
git push origin dev
```

### Creating Feature Branches
```bash
# Start new feature from dev
git checkout dev
git pull origin dev
git checkout -b feature/user-authentication

# Work on your feature...
git add .
git commit -m "Add user authentication endpoints"
git push origin feature/user-authentication

# Create PR to merge into dev
```

### Merging to Main (Production)
```bash
# After thorough testing on dev
git checkout main
git pull origin main
git merge dev
git push origin main
git tag -a v1.0.0 -m "First production release"
git push origin v1.0.0
```


## Next Steps

1. Start with user model and authentication
2. Set up JWT authentication middleware
3. Create your first feature branch
4. Build out each module (user → discover → carbon → etc.)
5. Write tests as you go
6. Set up CI/CD pipeline (GitHub Actions)