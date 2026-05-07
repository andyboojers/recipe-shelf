import sqlite3
import os
import json

DB_PATH = "/data/recipes.db"

def get_db():
    os.makedirs("/data", exist_ok=True)
    os.makedirs("/data/drafts", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Cache for recipes synced from Google Drive
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes_cache (
            id TEXT PRIMARY KEY,
            title TEXT,
            ingredients TEXT,
            instructions TEXT,
            notes TEXT,
            drive_file_id TEXT,
            image_drive_id TEXT,
            raw_ocr_text TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Temporary drafts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            title TEXT,
            ingredients TEXT,
            instructions TEXT,
            notes TEXT,
            image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def save_draft(draft_id: str, title: str, ingredients: list, instructions: list, notes: str, image_path: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO drafts (id, title, ingredients, instructions, notes, image_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        draft_id,
        title,
        json.dumps(ingredients) if ingredients else "[]",
        json.dumps(instructions) if instructions else "[]",
        notes,
        image_path
    ))
    conn.commit()
    conn.close()

def get_draft(draft_id: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": json.loads(row["ingredients"]) if row["ingredients"] else [],
        "instructions": json.loads(row["instructions"]) if row["instructions"] else [],
        "notes": row["notes"],
        "image_path": row["image_path"]
    }

def delete_draft(draft_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()

def save_recipe_cache(recipe_id: str, title: str, ingredients: list, instructions: list, notes: str, drive_file_id: str, image_drive_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO recipes_cache (id, title, ingredients, instructions, notes, drive_file_id, image_drive_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        recipe_id,
        title,
        json.dumps(ingredients) if ingredients else "[]",
        json.dumps(instructions) if instructions else "[]",
        notes,
        drive_file_id,
        image_drive_id
    ))
    conn.commit()
    conn.close()
