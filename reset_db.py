"""Run this once to delete the old DB and let Flask recreate it fresh."""
import os
db_path = os.path.join(os.path.dirname(__file__), "database", "puzzle_game.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted: {db_path}")
else:
    print("No DB found - Flask will create one fresh on next run.")
print("Now run: python app.py")
