import os
import sqlite3
 
from flask import Flask, jsonify, request
from flask_cors import CORS
 
app = Flask(__name__)
CORS(app)  # lets the browser page (another origin) call this API
 
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.db")
 
 
# ---------- Database functions ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn
 
 
def init_db():
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS items (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   done INTEGER NOT NULL DEFAULT 0
               )"""
        )
 
 
def row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
 
 
def list_items():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]
 
 
def add_item(title):
    with get_db() as conn:
        cur = conn.execute("INSERT INTO items (title) VALUES (?)", (title,))
        row = conn.execute("SELECT * FROM items WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)
 
 
def update_item(item_id, title=None, done=None):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            return None
        new_title = title if title is not None else row["title"]
        new_done = int(done) if done is not None else row["done"]
        conn.execute(
            "UPDATE items SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, item_id),
        )
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return row_to_dict(row)
 
 
def delete_item(item_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    return cur.rowcount > 0
 
 
# ---------- API routes ----------
@app.route("/")
def home():
    return jsonify({"message": "To-do API is running. Try /items"})
 
 
@app.route("/items", methods=["GET"])
def get_items():
    return jsonify(list_items())
 
 
@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    return jsonify(add_item(title)), 201
 
 
@app.route("/items/<int:item_id>", methods=["PUT"])
def edit_item(item_id):
    data = request.get_json(silent=True) or {}
    item = update_item(item_id, data.get("title"), data.get("done"))
    if item is None:
        return jsonify({"error": "item not found"}), 404
    return jsonify(item)
 
 
@app.route("/items/<int:item_id>", methods=["DELETE"])
def remove_item(item_id):
    if not delete_item(item_id):
        return jsonify({"error": "item not found"}), 404
    return jsonify({"deleted": item_id})
 
 
init_db()  # runs on import so it also works under gunicorn
 
if __name__ == "__main__":
    app.run(debug=True)
 