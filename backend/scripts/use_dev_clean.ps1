# backend/scripts/use_dev_clean.ps1

$env:DATABASE_URL = "postgresql+psycopg2://sns_user:$env:PGPASSWORD@127.0.0.1:5433/sns_emr_dev_clean"
Write-Host "DATABASE_URL set to sns_emr_dev_clean"

python -c "from sqlalchemy import text; from app.core.database import SessionLocal; db=SessionLocal(); print(db.execute(text('SELECT current_database(), current_user')).fetchall())"