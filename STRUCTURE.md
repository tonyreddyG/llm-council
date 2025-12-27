# LLM Council - Project Structure

```
llm-council/
├── backend/              # FastAPI backend application
│   ├── __init__.py
│   ├── main.py          # Main FastAPI app & routes
│   ├── auth.py          # Authentication & password hashing (PBKDF2)
│   ├── storage.py       # JSON file storage
│   └── council.py       # LLM council logic
│
├── frontend/            # React + Vite frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── api.js       # API client
│   │   └── App.jsx      # Main app component
│   ├── index.html
│   └── package.json
│
├── tests/               # Test files
│   ├── test_auth_flow.py
│   ├── test_login.py
│   └── test_long_pw.py
│
├── scripts/             # Utility scripts
│   ├── generate_certs.py # SSL certificate generator
│   └── README.md
│
├── certs/               # SSL certificates (gitignored)
│   ├── cert.pem
│   └── key.pem
│
├── data/                # Application data (gitignored)
│   ├── users.json
│   └── conversations.json
│
├── .venv/               # Python virtual environment
├── pyproject.toml       # Python dependencies
├── uv.lock              # Lock file
├── start.sh             # Startup script
├── .gitignore
├── .env                 # Environment variables (gitignored)
└── README.md
```

## Directory Guidelines

- **backend/**: Core backend application code only
- **frontend/**: Frontend application  code only
- **tests/**: All test files (unit, integration, e2e)
- **scripts/**: Utility scripts for development/deployment
- **certs/**: SSL certificates (not committed to git)
- **data/**: Runtime data files (not committed to git)
- **Root**: Only essential project config files (pyproject.toml, .gitignore, README, start script)
