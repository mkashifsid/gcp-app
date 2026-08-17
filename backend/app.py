import os
import datetime

from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, connect_timeout=5
    )


@app.route("/")
def health():
    return jsonify(status="ok"), 200


@app.route("/api/dbtime")
def db_time():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        now = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify(db_time=str(now), host=DB_HOST)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/api/init")
def init_table():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY, visited_at TIMESTAMP DEFAULT NOW());"
        )
        cur.execute("INSERT INTO visits DEFAULT VALUES RETURNING id;")
        visit_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(message="visit recorded", visit_id=visit_id)
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
