
"""
Campus Connect - Integrated Student Enrollment and Information System
Backend: Python + Flask + SQLite REST API

Combines:
  * Laboratory 3 - Student Course Management API (courses endpoints)
  * Laboratory 4 - Campus Connect Student Information Portal (students,
    enrollments, announcements, dashboard statistics)

Run locally:   python app.py
Then browse:   http://127.0.0.1:5000
API base URL:  http://127.0.0.1:5000/api
"""

import os
import sqlite3
from datetime import date, datetime

from flask import Flask, g, jsonify, render_template, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("CAMPUS_CONNECT_DB", os.path.join(BASE_DIR, "database.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "campus-connect-development-key")

# The Base44 frontend runs on a different origin, so the API must allow CORS.
CORS(app, resources={r"/api/*": {"origins": "*"}})

ENROLLMENT_STATUSES = ("Pending", "Approved", "Rejected", "Cancelled")
STUDENT_FIELDS = ("first_name", "last_name", "email", "program", "year_level")
COURSE_FIELDS = ("course_code", "course_name", "department")
ANNOUNCEMENT_FIELDS = ("title", "content", "author")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    program         TEXT NOT NULL,
    year_level      TEXT NOT NULL,
    contact_number  TEXT,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS courses (
    course_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code  TEXT NOT NULL UNIQUE,
    course_name  TEXT NOT NULL,
    department   TEXT NOT NULL,
    capacity     INTEGER NOT NULL DEFAULT 40,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id       INTEGER NOT NULL,
    course_id        INTEGER NOT NULL,
    enrollment_date  TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses (course_id)  ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS announcements (
    announcement_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    content          TEXT NOT NULL,
    date_posted      TEXT NOT NULL,
    author           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    full_name      TEXT NOT NULL,
    role           TEXT NOT NULL DEFAULT 'student',
    student_id     INTEGER,
    FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_enrollment_student ON enrollments (student_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_course  ON enrollments (course_id);
"""

ENROLLMENT_SELECT = """
SELECT e.enrollment_id, e.student_id, e.course_id, e.enrollment_date, e.status,
       s.first_name || ' ' || s.last_name AS student_name,
       s.program                          AS program,
       c.course_code                      AS course_code,
       c.course_name                      AS course_name,
       c.department                       AS department
FROM enrollments e
"""
