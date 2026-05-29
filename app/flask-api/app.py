import os
import time
import mysql.connector
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "flask_user"),
        password=os.environ.get("DB_PASSWORD", "flaskpass"),
        database=os.environ.get("DB_NAME", "assignment3db"),
    )


def init_db():
    retries = 30
    while retries > 0:
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully")
            return
        except Exception as e:
            print(f"DB not ready ({e}), retrying in 2s... ({retries} attempts left)")
            retries -= 1
            time.sleep(2)
    raise RuntimeError("Could not connect to database after 30 attempts")


@app.route("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/items", methods=["GET"])
def get_items():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    for item in items:
        if item.get("created_at"):
            item["created_at"] = item["created_at"].isoformat()
    return jsonify(items)


@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    if item.get("created_at"):
        item["created_at"] = item["created_at"].isoformat()
    return jsonify(item)


@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Field 'name' is required"}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (name, description) VALUES (%s, %s)",
        (data["name"], data.get("description", "")),
    )
    conn.commit()
    item_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"id": item_id, "message": "Item created"}), 201


@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE items SET name = %s, description = %s WHERE id = %s",
        (data.get("name"), data.get("description"), item_id),
    )
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    if affected == 0:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"message": "Item updated"})


@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    if affected == 0:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"message": "Item deleted"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
