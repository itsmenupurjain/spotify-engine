#!/usr/bin/env python3
"""
🚀 One-command project setup script.

Usage:
    python scripts/setup.py [--seed] [--dev] [--migrate]

Options:
    --seed      Load synthetic seed data (no API keys needed)
    --dev       Start development servers after setup
    --migrate   Run Alembic migrations
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def run(cmd: list, cwd=None, check=True):
    """Run a shell command and print output."""
    print(f"\n🔧 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or ROOT_DIR, check=check, text=True)
    return result


def check_prerequisites():
    """Check required tools are installed."""
    print("\n📋 Checking prerequisites...")
    tools = {
        "python": ["python", "--version"],
        "pip": ["pip", "--version"],
        "docker": ["docker", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
    }

    missing = []
    for name, cmd in tools.items():
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"   ✅ {name}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"   ❌ {name} — not found")
            missing.append(name)

    if missing:
        print(f"\n❌ Missing tools: {missing}. Please install them first.")
        sys.exit(1)


def setup_env():
    """Create .env from .env.example if not exists."""
    env_file = ROOT_DIR / ".env"
    example_file = ROOT_DIR / ".env.example"

    if not env_file.exists():
        print("\n📄 Creating .env from .env.example...")
        env_file.write_text(example_file.read_text())
        print("   ✅ .env created — please fill in your API keys!")
    else:
        print("\n   ℹ️  .env already exists, skipping")


def start_database():
    """Start PostgreSQL with pgvector using Docker Compose."""
    print("\n🐘 Starting PostgreSQL + pgvector...")
    run(["docker", "compose", "up", "-d", "db"])
    print("   ✅ Database started on port 5432")

    # Wait for DB to be ready
    import time
    print("   ⏳ Waiting for DB to be ready...")
    for i in range(30):
        result = subprocess.run(
            ["docker", "exec", "spotify_db", "pg_isready", "-U", "spotify"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("   ✅ Database is ready!")
            return
        time.sleep(2)
    print("   ⚠️  Database may not be fully ready. Proceeding anyway...")


def install_backend_deps():
    """Install Python backend dependencies."""
    print("\n🐍 Installing backend dependencies...")
    run(["pip", "install", "-r", "requirements.txt"], cwd=BACKEND_DIR)
    print("   ✅ Backend deps installed")


def install_frontend_deps():
    """Install Node.js frontend dependencies."""
    print("\n📦 Installing frontend dependencies...")
    run(["npm", "install"], cwd=FRONTEND_DIR)
    print("   ✅ Frontend deps installed")


def run_migrations():
    """Apply Alembic database migrations."""
    print("\n🗄️  Running database migrations...")
    run(["alembic", "upgrade", "head"], cwd=BACKEND_DIR)
    print("   ✅ Migrations applied")


def load_seed_data():
    """Generate and load synthetic seed data."""
    print("\n🌱 Generating seed data...")
    seed_file = ROOT_DIR / "scripts" / "seed_output.json"
    run(["python", str(ROOT_DIR / "scripts" / "seed_data.py")])
    print("   ✅ Seed data generated")

    print("\n📥 Loading seed data into database...")
    run([
        "python", "-c",
        f"""
import asyncio
import sys
sys.path.insert(0, '{BACKEND_DIR}')

async def load():
    from app.database import AsyncSessionLocal
    from app.pipeline.orchestrator import PipelineOrchestrator

    async with AsyncSessionLocal() as db:
        orch = PipelineOrchestrator(db)
        result = await orch.load_seed_data('{seed_file}')
        await db.commit()
        print(result)

asyncio.run(load())
"""
    ])
    print("   ✅ Seed data loaded")


def start_dev_servers():
    """Start backend and frontend dev servers."""
    print("\n🚀 Starting development servers...")
    print("   📡 Backend:  http://localhost:8000")
    print("   🎨 Frontend: http://localhost:3000")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("\n   Press Ctrl+C to stop\n")

    backend_proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR
    )
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR
    )

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n⛔ Stopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()


def main():
    parser = argparse.ArgumentParser(description="Spotify Discovery Engine Setup")
    parser.add_argument("--seed", action="store_true", help="Load seed data")
    parser.add_argument("--dev", action="store_true", help="Start dev servers after setup")
    parser.add_argument("--migrate", action="store_true", help="Run migrations")
    parser.add_argument("--all", action="store_true", help="Full setup: deps + DB + migrations + seed + dev")
    args = parser.parse_args()

    if args.all:
        args.seed = args.migrate = args.dev = True

    print("=" * 60)
    print("🎵 Spotify Discovery Engine — Setup")
    print("=" * 60)

    check_prerequisites()
    setup_env()
    start_database()
    install_backend_deps()
    install_frontend_deps()

    if args.migrate:
        run_migrations()

    if args.seed:
        load_seed_data()

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📋 Quick start:")
    print("   1. Edit .env with your API keys")
    print("   2. cd backend && alembic upgrade head  (if not done)")
    print("   3. uvicorn app.main:app --reload --port 8000")
    print("   4. cd frontend && npm run dev")
    print("   5. Open http://localhost:3000")

    if args.dev:
        start_dev_servers()


if __name__ == "__main__":
    main()
