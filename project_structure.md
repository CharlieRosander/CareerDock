app/
├── api/                       # All REST API logik
│   ├── v1/                   # API version 1
│   │   ├── endpoints/        # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── jobs.py
│   │   │   └── ...
│   │   └── router.py         # Samlar alla v1 routes
├── models/                    # Database models
│   ├── job.py
│   ├── user.py
│   └── ...
├── schemas/                   # Pydantic models för API
│   ├── job.py
│   ├── user.py
│   └── ...
├── services/                  # Business logic
│   ├── auth_service.py
│   ├── job_service.py
│   └── ...
├── core/                     # Core functionality
│   ├── config.py
│   ├── security.py
│   └── database.py
├── templates/                # Frontend (oförändrad)
│   ├── base.html
│   ├── job_registry.html
│   └── ...
└── static/                   # Static files (oförändrad)
    ├── css/
    └── js/