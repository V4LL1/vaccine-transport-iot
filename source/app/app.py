from flask import Flask, jsonify, render_template
import mysql.connector
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

DB = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",   # <<< coloque sua senha aqui
    "database": "vaccine_transport"
}

def db():
    return mysql.connector.connect(**DB)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/trips")
def trips():
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT t.trip_id, t.start_time, t.end_time, t.origin, t.destination,
               b.batch_code, v.name AS vaccine_name
        FROM trips t
        JOIN vaccine_batch b ON t.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        ORDER BY t.start_time DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route("/api/readings/<int:trip_id>")
def readings(trip_id):
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.timestamp, r.temperature, r.humidity, r.latitude, r.longitude,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN vaccine_batch b ON r.batch_id = b.batch_id
        JOIN vaccines v ON b.vaccine_id = v.vaccine_id
        WHERE r.trip_id = %s
        ORDER BY r.timestamp ASC
    """, (trip_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route("/api/readings/recent")
def recent_readings():
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.timestamp, r.temperature, r.humidity, r.latitude, r.longitude,
               t.trip_id, b.batch_code
        FROM readings r
        JOIN trips t ON r.trip_id = t.trip_id
        JOIN vaccine_batch b ON r.batch_id = b.batch_id
        ORDER BY r.timestamp DESC
        LIMIT 20
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
