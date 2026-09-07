#!/usr/bin/env python3
"""
git_research.py — Адаптер до сервісу dnk_git_research та PostgreSQL pgvector
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Завантаження .env
PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = PROJECT_ROOT / "services/dnk_git_research/.env"
load_dotenv(ENV_PATH)
sys.path.insert(0, str(PROJECT_ROOT))

class GitResearchAdapter:
    def __init__(self):
        self.postgres_url = os.environ.get("POSTGRES_URL")

    def query_patterns(self, query: str, limit: int = 5) -> list[dict]:
        """Шукає корисні патерни коду та рішень у базі знань pgvector"""
        if not self.postgres_url:
            return []
            
        import psycopg2
        results = []
        try:
            conn = psycopg2.connect(self.postgres_url)
            with conn.cursor() as cur:
                # Пошук репозиторіїв та рішень за текстовим збігом або тегами
                cur.execute("""
                    SELECT r.full_name, r.url, r.description, d.summary_ua, d.use_cases
                    FROM repositories r
                    LEFT JOIN dossiers d ON r.id = d.repository_id
                    WHERE LOWER(r.description) LIKE %s OR LOWER(r.full_name) LIKE %s
                    LIMIT %s
                """, (f"%{query.lower()}%", f"%{query.lower()}%", limit))
                
                for row in cur.fetchall():
                    results.append({
                        "full_name": row[0],
                        "url": row[1],
                        "description": row[2],
                        "summary_ua": row[3],
                        "use_cases": row[4]
                    })
            conn.close()
        except Exception as e:
            print(f"[!] Помилка адаптера GitResearch: {e}")
        return results

if __name__ == "__main__":
    adapter = GitResearchAdapter()
    print("Тест пошуку патернів 'quiz':")
    print(json.dumps(adapter.query_patterns("quiz", limit=2), indent=2, ensure_ascii=False))
