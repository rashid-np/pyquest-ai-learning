"""
migrate_db.py — Safe migration: adds topic_progress column to existing DB.
Run this INSTEAD of reset_db.py if you want to keep existing user data.
If you have a fresh install, reset_db.py works fine too.
"""
import os, sqlite3

db_path = os.path.join(os.path.dirname(__file__), "database", "puzzle_game.db")

if not os.path.exists(db_path):
    print("No DB found. Run: python app.py  (it will create a fresh one)")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cur.fetchall()]
    if "topic_progress" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN topic_progress TEXT DEFAULT '{}'")
        conn.commit()
        print("Added topic_progress column — all existing user scores preserved!")
    else:
        print("topic_progress column already exists — nothing to do.")
    conn.close()
    print("Migration complete. Run: python app.py")
