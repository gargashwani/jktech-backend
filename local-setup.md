   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   cp .env.example .env
   # Edit .env with your database credentials
   alembic upgrade head
   python main.py




cd frontend
   npm install
   cp .env.example .env
   npm run dev