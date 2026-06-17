import sqlite3
import os
import json

DATA_DIR = os.environ.get("DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "recipes.db")

def get_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "drafts"), exist_ok=True)
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
            servings TEXT,
            cooking_time TEXT,
            tags TEXT,
            drive_file_id TEXT,
            image_drive_id TEXT,
            original_drive_id TEXT,
            raw_ocr_text TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # FTS5 search index
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS recipe_search USING fts5(
            id UNINDEXED,
            title,
            ingredients,
            instructions,
            notes,
            servings,
            cooking_time,
            tags,
            raw_ocr_text
        )
    """)
    
    # Triggers for syncing recipes_cache with recipe_search
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS recipes_cache_ai AFTER INSERT ON recipes_cache BEGIN
            INSERT INTO recipe_search(id, title, ingredients, instructions, notes, servings, cooking_time, tags, raw_ocr_text)
            VALUES (new.id, new.title, new.ingredients, new.instructions, new.notes, new.servings, new.cooking_time, new.tags, new.raw_ocr_text);
        END;
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS recipes_cache_au AFTER UPDATE ON recipes_cache BEGIN
            UPDATE recipe_search SET
                title = new.title,
                ingredients = new.ingredients,
                instructions = new.instructions,
                notes = new.notes,
                servings = new.servings,
                cooking_time = new.cooking_time,
                tags = new.tags,
                raw_ocr_text = new.raw_ocr_text
            WHERE id = old.id;
        END;
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS recipes_cache_ad AFTER DELETE ON recipes_cache BEGIN
            DELETE FROM recipe_search WHERE id = old.id;
        END;
    """)
    
    # Temporary drafts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            title TEXT,
            ingredients TEXT,
            instructions TEXT,
            notes TEXT,
            servings TEXT,
            cooking_time TEXT,
            tags TEXT,
            image_path TEXT,
            original_image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # File cache tracking for LRU
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_cache (
            drive_file_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Run migrations for existing databases
    try:
        cursor.execute("ALTER TABLE drafts ADD COLUMN original_image_path TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE recipes_cache ADD COLUMN original_drive_id TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def save_draft(draft_id: str, title: str, ingredients: list, instructions: list, notes: str, servings: str, cooking_time: str, tags: list, image_path: str, original_image_paths: list = None):
    original_image_paths = original_image_paths or []
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO drafts (id, title, ingredients, instructions, notes, servings, cooking_time, tags, image_path, original_image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        draft_id,
        title,
        json.dumps(ingredients) if ingredients else "[]",
        json.dumps(instructions) if instructions else "[]",
        notes,
        servings,
        cooking_time,
        json.dumps(tags) if tags else "[]",
        image_path,
        json.dumps(original_image_paths)
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
        "servings": row["servings"],
        "cooking_time": row["cooking_time"],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "image_path": row["image_path"],
        "original_image_paths": json.loads(row["original_image_path"]) if "original_image_path" in row.keys() and row["original_image_path"] and row["original_image_path"].startswith("[") else ([row["original_image_path"]] if "original_image_path" in row.keys() and row["original_image_path"] else [])
    }

def delete_draft(draft_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()

def save_recipe_cache(recipe_id: str, title: str, ingredients: list, instructions: list, notes: str, servings: str, cooking_time: str, tags: list, drive_file_id: str, image_drive_id: str, original_drive_ids: list = None):
    original_drive_ids = original_drive_ids or []
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO recipes_cache (id, title, ingredients, instructions, notes, servings, cooking_time, tags, drive_file_id, image_drive_id, original_drive_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        recipe_id,
        title,
        json.dumps(ingredients) if ingredients else "[]",
        json.dumps(instructions) if instructions else "[]",
        notes,
        servings,
        cooking_time,
        json.dumps(tags) if tags else "[]",
        drive_file_id,
        image_drive_id,
        json.dumps(original_drive_ids)
    ))
    conn.commit()
    conn.close()

def get_recipe(recipe_id: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes_cache WHERE id = ?", (recipe_id,))
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
        "servings": row["servings"],
        "cooking_time": row["cooking_time"],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "drive_file_id": row["drive_file_id"],
        "image_drive_id": row["image_drive_id"],
        "original_drive_ids": json.loads(row["original_drive_id"]) if "original_drive_id" in row.keys() and row["original_drive_id"] and row["original_drive_id"].startswith("[") else ([row["original_drive_id"]] if "original_drive_id" in row.keys() and row["original_drive_id"] else []),
        "last_updated": row["last_updated"]
    }

def delete_recipe(recipe_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes_cache WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

def search_recipes(query: str) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    safe_query = query.replace('"', '""')
    match_str = f'"{safe_query}"*'
    cursor.execute("""
        SELECT r.* 
        FROM recipes_cache r
        JOIN recipe_search s ON r.id = s.id
        WHERE recipe_search MATCH ?
        ORDER BY rank
    """, (match_str,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "title": row["title"],
            "ingredients": json.loads(row["ingredients"]) if row["ingredients"] else [],
            "instructions": json.loads(row["instructions"]) if row["instructions"] else [],
            "notes": row["notes"],
            "servings": row["servings"],
            "cooking_time": row["cooking_time"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "drive_file_id": row["drive_file_id"],
            "image_drive_id": row["image_drive_id"],
            "original_drive_ids": json.loads(row["original_drive_id"]) if "original_drive_id" in row.keys() and row["original_drive_id"] and row["original_drive_id"].startswith("[") else ([row["original_drive_id"]] if "original_drive_id" in row.keys() and row["original_drive_id"] else []),
            "last_updated": row["last_updated"]
        })
    return results

def get_cached_file(drive_file_id: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    # Update last_accessed timestamp to keep it fresh (LRU)
    from datetime import datetime, timezone
    cursor.execute("""
        UPDATE file_cache 
        SET last_accessed = ? 
        WHERE drive_file_id = ?
    """, (datetime.now(timezone.utc).isoformat(), drive_file_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM file_cache WHERE drive_file_id = ?", (drive_file_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "drive_file_id": row["drive_file_id"],
        "file_path": row["file_path"],
        "file_size": row["file_size"],
        "last_accessed": row["last_accessed"]
    }

def add_cached_file(drive_file_id: str, file_path: str, file_size: int):
    conn = get_db()
    cursor = conn.cursor()
    from datetime import datetime, timezone
    cursor.execute("""
        INSERT OR REPLACE INTO file_cache (drive_file_id, file_path, file_size, last_accessed)
        VALUES (?, ?, ?, ?)
    """, (drive_file_id, file_path, file_size, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def get_total_cache_size() -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(file_size) FROM file_cache")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row[0] is not None else 0

def get_oldest_cached_files(limit: int) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM file_cache 
        ORDER BY last_accessed ASC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "drive_file_id": row["drive_file_id"],
            "file_path": row["file_path"],
            "file_size": row["file_size"],
            "last_accessed": row["last_accessed"]
        })
    return results

def delete_cached_file(drive_file_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM file_cache WHERE drive_file_id = ?", (drive_file_id,))
    conn.commit()
    conn.close()
