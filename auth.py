import hashlib
import secrets
import sqlite3
from database import get_connection


def hash_password(password):
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return salt + "$" + pwdhash.hex()


def verify_password(password, stored):
    salt, pwdhash = stored.split("$")
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex() == pwdhash


def customer_register(first_name, middle_name, last_name, email, phone, password):
    if not first_name or not first_name.strip():
        return False, "First name is required."
    if not last_name or not last_name.strip():
        return False, "Last name is required."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not email and not phone:
        return False, "Email or phone number is required."

    full_name = " ".join(
        part for part in [first_name.strip(), middle_name.strip() if middle_name else None, last_name.strip()] if part
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id FROM users WHERE (email = ? AND email IS NOT NULL) OR (phone = ? AND phone IS NOT NULL)",
            (email if email else None, phone if phone else None))
        if cur.fetchone():
            return False, "An account with this email or phone already exists."
        cur.execute(
            "INSERT INTO users (first_name, middle_name, last_name, email, phone, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name.strip(), middle_name.strip() if middle_name else None,
             last_name.strip(), email if email else None, phone if phone else None,
             hash_password(password)))
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "An account with this email or phone already exists."
    finally:
        conn.close()


def customer_login(email_or_phone, password):
    if not email_or_phone or not password:
        return False, "Please enter email/phone and password."
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, first_name, middle_name, last_name, email, phone, password_hash, is_active FROM users "
            "WHERE (email = ? OR phone = ?)", (email_or_phone, email_or_phone))
        row = cur.fetchone()
        if not row:
            return False, "Invalid email/phone or password."
        if not row["is_active"]:
            return False, "Account is deactivated."
        if not verify_password(password, row["password_hash"]):
            return False, "Invalid email/phone or password."
        full_name = " ".join(
            part for part in [row["first_name"], row["middle_name"], row["last_name"]] if part
        )
        return True, {
            "user_id": row["user_id"],
            "first_name": row["first_name"],
            "middle_name": row["middle_name"],
            "last_name": row["last_name"],
            "full_name": full_name,
            "email": row["email"],
            "phone": row["phone"],
        }
    finally:
        conn.close()


def admin_login(username, password):
    if not username or not password:
        return False, "Please enter username and password."
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT admin_id, full_name, username, password_hash, is_active FROM admins WHERE username = ?",
            (username,))
        row = cur.fetchone()
        if not row or not row["is_active"]:
            return False, "Invalid admin account."
        if not verify_password(password, row["password_hash"]):
            return False, "Invalid username or password."
        return True, {
            "admin_id": row["admin_id"],
            "full_name": row["full_name"],
            "username": row["username"],
        }
    finally:
        conn.close()


def admin_exists():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM admins")
        return cur.fetchone()[0] > 0
    finally:
        conn.close()


def create_admin(full_name, username, password):
    if not full_name or not username or not password:
        return False, "All fields are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT admin_id FROM admins WHERE username = ?", (username,))
        if cur.fetchone():
            return False, "Username already exists."
        cur.execute(
            "INSERT INTO admins (full_name, username, password_hash) VALUES (?, ?, ?)",
            (full_name.strip(), username.strip(), hash_password(password)))
        conn.commit()
        return True, "Admin account created successfully."
    finally:
        conn.close()
