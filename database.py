import os
import sqlite3
from datetime import datetime, timedelta

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tattoo_booking.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PKG_IMG_DIR = os.path.join(ASSETS_DIR, "package_images")
ARTIST_IMG_DIR = os.path.join(ASSETS_DIR, "artist_images")
REF_IMG_DIR = os.path.join(ASSETS_DIR, "customer_references")

PLACEHOLDER_PKG = os.path.join(PKG_IMG_DIR, "placeholder.jpg")
PLACEHOLDER_ARTIST = os.path.join(ARTIST_IMG_DIR, "placeholder.jpg")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_dirs():
    for d in (ASSETS_DIR, PKG_IMG_DIR, ARTIST_IMG_DIR, REF_IMG_DIR):
        os.makedirs(d, exist_ok=True)


def create_placeholder_image(path, text, size=(400, 300)):
    if Image is None:
        open(path, "wb").close()
        return
    img = Image.new("RGB", size, (36, 36, 36))
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, size[0] - 8, size[1] - 8], outline=(245, 34, 45), width=2)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((size[0] - w) // 2, (size[1] - h) // 2), text, fill=(245, 245, 245), font=font)
    img.save(path)


def init_database():
    """Create tables and insert sample data if missing. Safe to run on every start."""
    ensure_dirs()
    create_placeholder_image(PLACEHOLDER_PKG, "Package Image")
    create_placeholder_image(PLACEHOLDER_ARTIST, "Artist")

    conn = get_connection()
    try:
        cur = conn.cursor()

        sql_path = os.path.join(BASE_DIR, "database.sql")
        if os.path.exists(sql_path):
            with open(sql_path, "r", encoding="utf-8") as f:
                schema = f.read()
            cur.executescript(schema)
        conn.commit()

        migrate_users_table(cur)
        migrate_packages_table(cur)
        migrate_image_extensions(cur)
        insert_sample_data(cur)
        create_default_admin(cur)
        conn.commit()
    finally:
        conn.close()


def migrate_image_extensions(cur):
    """Point stored image paths at the .jpg artwork (was previously .png)."""
    for column, table in (("image_path", "packages"), ("profile_image", "artists")):
        cur.execute(
            "UPDATE {t} SET {c} = REPLACE({c}, '.png', '.jpg') "
            "WHERE {c} IS NOT NULL AND LOWER({c}) LIKE '%.png'".format(t=table, c=column))


def migrate_packages_table(cur):
    """Add the ``kind`` column (Package / Tattoo) to existing databases."""
    cur.execute("PRAGMA table_info(packages)")
    columns = {row[1] for row in cur.fetchall()}
    if columns and "kind" not in columns:
        cur.execute("ALTER TABLE packages ADD COLUMN kind TEXT NOT NULL DEFAULT 'Package'")


def migrate_users_table(cur):
    """Migrate existing users table from full_name to first/middle/last name columns."""
    # Check existing columns
    cur.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cur.fetchall()}

    if "full_name" in columns and "first_name" not in columns:
        # Add new columns
        cur.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN middle_name TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN last_name TEXT")

        # Populate new columns from full_name
        cur.execute("SELECT user_id, full_name FROM users")
        for row in cur.fetchall():
            user_id, full_name = row[0], row[1]
            parts = (full_name or "").split(" ", 2)
            first = parts[0] if len(parts) > 0 else ""
            middle = parts[1] if len(parts) > 1 else None
            last = parts[2] if len(parts) > 2 else (parts[1] if len(parts) == 2 else "")
            cur.execute(
                "UPDATE users SET first_name = ?, middle_name = ?, last_name = ? WHERE user_id = ?",
                (first, middle, last, user_id))

        # Drop the old full_name column by recreating the table
        # SQLite doesn't support DROP COLUMN directly in older versions, so we recreate
        cur.execute("""
            CREATE TABLE users_new (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                CHECK (email IS NOT NULL OR phone IS NOT NULL)
            )
        """)
        cur.execute(
            "INSERT INTO users_new (user_id, first_name, middle_name, last_name, email, phone, password_hash, created_at, is_active) "
            "SELECT user_id, first_name, middle_name, last_name, email, phone, password_hash, created_at, is_active FROM users")
        cur.execute("DROP TABLE users")
        cur.execute("ALTER TABLE users_new RENAME TO users")
        # Recreate indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")


def create_default_admin(cur):
    """Create a default admin account if none exists. Change credentials after first login."""
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        from auth import hash_password
        cur.execute(
            "INSERT INTO admins (full_name, username, password_hash) VALUES (?, ?, ?)",
            ("Studio Administrator", "admin", hash_password("admin123")))


def insert_sample_data(cur):
    # --- Packages ---
    cur.execute("SELECT COUNT(*) FROM packages")
    if cur.fetchone()[0] == 0:
        packages = [
            ("Traditional Sleeve",
             "Classic bold traditional tattoo sleeve covering the full arm.",
             "Traditional", 450.00, 360, "traditional_sleeve.jpg"),
            ("Minimalist Line Work",
             "Clean, delicate line work tattoo perfect for small placements.",
             "Minimalist", 120.00, 60, "minimalist_line.jpg"),
            ("Watercolor Rose",
             "Vibrant watercolor style rose tattoo with soft color blending.",
             "Watercolor", 250.00, 120, "watercolor_rose.jpg"),
            ("Blackwork Geometric",
             "Sharp blackwork geometric patterns and shapes.",
             "Blackwork", 300.00, 150, "blackwork_geo.jpg"),
            ("Japanese Koi",
             "Traditional Japanese koi fish with waves and lotus.",
             "Japanese", 500.00, 240, "koi_fish.jpg"),
            ("Neo Traditional Panther",
             "Vivid neo-traditional panther with bold outlines.",
             "Neo Traditional", 380.00, 180, "panther.jpg"),
            ("Fineline Script",
             "Elegant fine line script text tattoo.",
             "Minimalist", 100.00, 45, "fineline_script.jpg"),
            ("Cover-up Tattoo",
             "Professional cover-up to refresh or hide old ink.",
             "Cover-up", 600.00, 300, "coverup.jpg"),
        ]
        for p in packages:
            cur.execute(
                "INSERT INTO packages (package_name, description, category, price, duration_minutes, image_path) "
                "VALUES (?, ?, ?, ?, ?, ?)", p)

    # --- Individual tattoos (bookable on their own, no package required) ---
    cur.execute("SELECT COUNT(*) FROM packages WHERE kind = 'Tattoo'")
    if cur.fetchone()[0] == 0:
        tattoos = [
            ("Japanese Koi — Single Tattoo",
             "A single koi fish tattoo with water details and bold irezumi outlines. "
             "Book the tattoo on its own — no package required.",
             "Japanese", 320.00, 180, "japanese.jpg"),
            ("Blackwork Mandala — Single Tattoo",
             "Solid black geometric mandala with fine dotwork shading as a standalone piece.",
             "Blackwork", 220.00, 150, "blackwork.jpg"),
            ("Realism Portrait — Single Tattoo",
             "Hyper realistic black and grey portrait study worked as a single session piece.",
             "Realism", 400.00, 240, "realism.jpg"),
            ("Fine Line Botanical — Single Tattoo",
             "Delicate single-needle botanical linework — light, airy and quick to heal.",
             "Fine Line", 120.00, 90, "fineline.jpg"),
            ("Geometric Band — Single Tattoo",
             "Symmetrical geometric band built from precise lines and stacked dotwork.",
             "Geometric", 200.00, 120, "geometric.jpg"),
            ("Traditional Swallow — Single Tattoo",
             "Classic American traditional swallow with bold colour and clean outlines.",
             "Traditional", 240.00, 150, "traditional.jpg"),
        ]
        for t in tattoos:
            cur.execute(
                "INSERT INTO packages (package_name, description, category, kind, price, duration_minutes, image_path) "
                "VALUES (?, ?, ?, 'Tattoo', ?, ?, ?)", t)

    # --- Artists ---
    cur.execute("SELECT COUNT(*) FROM artists")
    if cur.fetchone()[0] == 0:
        artists = [
            ("Marco Rivera",
             "10 years experience in traditional and neo-traditional styles.",
             "Traditional, Neo Traditional, Cover-up", "marco.jpg"),
            ("Elena Zhang",
             "Specialist in fine line, minimalist and watercolor tattoos.",
             "Minimalist, Watercolor, Fineline", "elena.jpg"),
            ("Jamal Owens",
             "Bold blackwork and geometric patterns specialist.",
             "Blackwork, Geometric, Tribal", "jamal.jpg"),
            ("Sofia Mendes",
             "Japanese style artist with focus on koi, dragons and sleeves.",
             "Japanese, Traditional", "sofia.jpg"),
        ]
        for a in artists:
            cur.execute(
                "INSERT INTO artists (full_name, bio, specialties, profile_image) VALUES (?, ?, ?, ?)", a)

    # --- Add-ons ---
    cur.execute("SELECT COUNT(*) FROM package_addons")
    if cur.fetchone()[0] == 0:
        addons = [
            ("Touch-up Session", "Free touch-up within 60 days", 0.00, 1),
            ("Custom Design Sketch", "Personalized design created before your appointment", 50.00, 1),
            ("Numbing Cream", "Topical numbing cream for comfort", 25.00, 1),
            ("Aftercare Kit", "Professional aftercare ointment and cleaning supplies", 30.00, 1),
            ("Extended Session", "Additional 30 minutes of tattoo time", 100.00, 1),
        ]
        for ad in addons:
            cur.execute(
                "INSERT INTO package_addons (addon_name, description, price, is_active) VALUES (?, ?, ?, ?)", ad)

    # --- Artist availability for next 14 days ---
    cur.execute("SELECT artist_id FROM artists WHERE is_active = 1")
    artist_ids = [r[0] for r in cur.fetchall()]
    if artist_ids:
        today = datetime.now().date()
        for aid in artist_ids:
            for i in range(14):
                d = today + timedelta(days=i)
                datestr = d.isoformat()
                cur.execute(
                    "INSERT OR IGNORE INTO artist_availability (artist_id, available_date, start_time, end_time, is_available) "
                    "VALUES (?, ?, ?, ?, 1)", (aid, datestr, "09:00", "13:00"))
                cur.execute(
                    "INSERT OR IGNORE INTO artist_availability (artist_id, available_date, start_time, end_time, is_available) "
                    "VALUES (?, ?, ?, ?, 1)", (aid, datestr, "14:00", "18:00"))


# ----------------------------------------------------------------------------
# Packages
# ----------------------------------------------------------------------------
def get_active_packages(kind="Package"):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM packages WHERE is_active = 1 AND kind = ? "
                    "ORDER BY package_name", (kind,))
        return cur.fetchall()
    finally:
        conn.close()


def get_all_packages_admin(kind="Package"):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM packages WHERE kind = ? ORDER BY package_name", (kind,))
        return cur.fetchall()
    finally:
        conn.close()


def get_package(package_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM packages WHERE package_id = ?", (package_id,))
        return cur.fetchone()
    finally:
        conn.close()


def get_categories(kind="Package"):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category FROM packages WHERE is_active = 1 AND kind = ? "
                    "ORDER BY category", (kind,))
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def search_packages(term, category, kind="Package"):
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM packages WHERE is_active = 1 AND kind = ?"
        params = [kind]
        if term:
            query += " AND (package_name LIKE ? OR description LIKE ?)"
            like = "%" + term + "%"
            params.extend([like, like])
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY package_name"
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()


def add_package(name, description, category, price, duration, image_path, kind="Package"):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO packages (package_name, description, category, kind, price, duration_minutes, image_path, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, description, category, kind, price, duration, image_path,
             datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_package(package_id, name, description, category, price, duration, image_path):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE packages SET package_name=?, description=?, category=?, price=?, duration_minutes=?, image_path=?, updated_at=? "
            "WHERE package_id=?",
            (name, description, category, price, duration, image_path, datetime.now().isoformat(), package_id))
        conn.commit()
    finally:
        conn.close()


def deactivate_package(package_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE packages SET is_active = 0, updated_at = ? WHERE package_id = ?",
                    (datetime.now().isoformat(), package_id))
        conn.commit()
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# Artists
# ----------------------------------------------------------------------------
def get_active_artists():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM artists WHERE is_active = 1 ORDER BY full_name")
        return cur.fetchall()
    finally:
        conn.close()


def get_all_artists_admin():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM artists ORDER BY full_name")
        return cur.fetchall()
    finally:
        conn.close()


def get_artist(artist_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM artists WHERE artist_id = ?", (artist_id,))
        return cur.fetchone()
    finally:
        conn.close()


def add_artist(full_name, bio, specialties, profile_image):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO artists (full_name, bio, specialties, profile_image) VALUES (?, ?, ?, ?)",
            (full_name, bio, specialties, profile_image))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_artist(artist_id, full_name, bio, specialties, profile_image):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE artists SET full_name=?, bio=?, specialties=?, profile_image=? WHERE artist_id=?",
            (full_name, bio, specialties, profile_image, artist_id))
        conn.commit()
    finally:
        conn.close()


def deactivate_artist(artist_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE artists SET is_active = 0 WHERE artist_id = ?", (artist_id,))
        conn.commit()
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# Availability
# ----------------------------------------------------------------------------
def get_availability(artist_id, date_str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM artist_availability WHERE artist_id = ? AND available_date = ? AND is_available = 1 "
            "ORDER BY start_time", (artist_id, date_str))
        return cur.fetchall()
    finally:
        conn.close()


def add_availability(artist_id, date_str, start_time, end_time):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO artist_availability (artist_id, available_date, start_time, end_time, is_available) "
            "VALUES (?, ?, ?, ?, 1)", (artist_id, date_str, start_time, end_time))
        conn.commit()
    finally:
        conn.close()


def get_booked_slots(artist_id, date_str, exclude_booking_id=None):
    """Return booked (Pending or Confirmed) start/end time ranges for an artist on a date."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if exclude_booking_id:
            cur.execute(
                "SELECT start_time, end_time FROM bookings WHERE artist_id = ? AND appointment_date = ? "
                "AND booking_status IN ('Pending','Confirmed') AND booking_id != ?",
                (artist_id, date_str, exclude_booking_id))
        else:
            cur.execute(
                "SELECT start_time, end_time FROM bookings WHERE artist_id = ? AND appointment_date = ? "
                "AND booking_status IN ('Pending','Confirmed')",
                (artist_id, date_str))
        return cur.fetchall()
    finally:
        conn.close()


def time_to_minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def add_minutes(t, minutes):
    total = time_to_minutes(t) + minutes
    return "{:02d}:{:02d}".format(total // 60, total % 60)


def is_slot_available(artist_id, date_str, start_time, end_time, exclude_booking_id=None):
    booked = get_booked_slots(artist_id, date_str, exclude_booking_id)
    for bs, be in booked:
        if time_to_minutes(start_time) < time_to_minutes(be) and time_to_minutes(bs) < time_to_minutes(end_time):
            return False
    return True


# ----------------------------------------------------------------------------
# Add-ons
# ----------------------------------------------------------------------------
def get_addons():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM package_addons WHERE is_active = 1 ORDER BY addon_name")
        return cur.fetchall()
    finally:
        conn.close()


def get_all_addons_admin():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM package_addons ORDER BY addon_name")
        return cur.fetchall()
    finally:
        conn.close()


def add_addon(name, description, price):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO package_addons (addon_name, description, price, is_active) VALUES (?, ?, ?, 1)",
                    (name, description, price))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def deactivate_addon(addon_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE package_addons SET is_active = 0 WHERE addon_id = ?", (addon_id,))
        conn.commit()
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# Bookings
# ----------------------------------------------------------------------------
def generate_reference():
    return "TAT-" + datetime.now().strftime("%Y%m%d%H%M%S%f")


def create_booking(user_id, package_id, artist_id, appointment_date, start_time,
                   placement, tattoo_size, design_description, reference_image_path,
                   customer_notes, addon_selections):
    """
    addon_selections: list of dicts {addon_id, quantity, unit_price}
    Creates booking + addons + status history in one transaction.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN")

        # Validate package & artist active
        cur.execute("SELECT price, duration_minutes FROM packages WHERE package_id = ? AND is_active = 1", (package_id,))
        pkg = cur.fetchone()
        if not pkg:
            conn.rollback()
            return False, "Package is not available.", None, None

        cur.execute("SELECT artist_id FROM artists WHERE artist_id = ? AND is_active = 1", (artist_id,))
        if not cur.fetchone():
            conn.rollback()
            return False, "Artist is not available.", None, None

        end_time = add_minutes(start_time, pkg["duration_minutes"])

        # Recheck availability to prevent double booking
        if not is_slot_available(artist_id, appointment_date, start_time, end_time):
            conn.rollback()
            return False, "This time slot is no longer available.", None, None

        base_price = pkg["price"]
        additional_cost = 0.0
        for a in addon_selections:
            additional_cost += float(a["unit_price"]) * int(a["quantity"])
        total_price = base_price + additional_cost

        reference = generate_reference()
        cur.execute(
            "INSERT INTO bookings (booking_reference, user_id, package_id, artist_id, appointment_date, start_time, "
            "end_time, placement, tattoo_size, design_description, reference_image_path, base_price, additional_cost, "
            "total_price, booking_status, payment_status, customer_notes, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', 'Pending', ?, ?)",
            (reference, user_id, package_id, artist_id, appointment_date, start_time, end_time, placement,
             tattoo_size, design_description, reference_image_path, base_price, additional_cost, total_price,
             customer_notes, datetime.now().isoformat()))
        booking_id = cur.lastrowid

        # Add-ons
        for a in addon_selections:
            cur.execute(
                "INSERT INTO booking_addons (booking_id, addon_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (booking_id, a["addon_id"], a["quantity"], a["unit_price"]))

        # Status history
        cur.execute(
            "INSERT INTO booking_status_history (booking_id, previous_status, new_status, notes, changed_at) "
            "VALUES (?, ?, 'Pending', ?, ?)",
            (booking_id, None, "Booking created by customer", datetime.now().isoformat()))

        conn.commit()
        return True, "Booking created successfully.", booking_id, reference
    except Exception as e:
        conn.rollback()
        return False, str(e), None, None
    finally:
        conn.close()


def get_booking(booking_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        return cur.fetchone()
    finally:
        conn.close()


def get_booking_by_reference(reference):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM bookings WHERE booking_reference = ?", (reference,))
        return cur.fetchone()
    finally:
        conn.close()


def get_bookings_by_user(user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT b.*, p.package_name, a.full_name AS artist_name FROM bookings b "
            "LEFT JOIN packages p ON b.package_id = p.package_id "
            "LEFT JOIN artists a ON b.artist_id = a.artist_id "
            "WHERE b.user_id = ? ORDER BY b.created_at DESC", (user_id,))
        return cur.fetchall()
    finally:
        conn.close()


def get_all_bookings_admin():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT b.*, u.first_name || COALESCE(' ' || u.middle_name, '') || ' ' || u.last_name AS customer_name, p.package_name, a.full_name AS artist_name FROM bookings b "
            "LEFT JOIN users u ON b.user_id = u.user_id "
            "LEFT JOIN packages p ON b.package_id = p.package_id "
            "LEFT JOIN artists a ON b.artist_id = a.artist_id "
            "ORDER BY b.created_at DESC")
        return cur.fetchall()
    finally:
        conn.close()


def get_booking_addons(booking_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ba.*, pa.addon_name FROM booking_addons ba "
            "LEFT JOIN package_addons pa ON ba.addon_id = pa.addon_id WHERE ba.booking_id = ?", (booking_id,))
        return cur.fetchall()
    finally:
        conn.close()


def cancel_booking(booking_id, user_id):
    """Customer cancels a Pending booking."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute(
            "SELECT booking_status FROM bookings WHERE booking_id = ? AND user_id = ?", (booking_id, user_id))
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return False, "Booking not found."
        if row["booking_status"] != "Pending":
            conn.rollback()
            return False, "Only Pending bookings can be cancelled."
        # Refund any deposit the customer already paid, mirroring the admin flow.
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments "
                    "WHERE booking_id = ? AND payment_status = 'Paid'", (booking_id,))
        settled = float(cur.fetchone()[0] or 0)
        if settled > 0:
            cur.execute("UPDATE payments SET payment_status = 'Refunded' "
                        "WHERE booking_id = ? AND payment_status = 'Paid'", (booking_id,))
        cur.execute("UPDATE bookings SET booking_status = 'Cancelled', updated_at = ? WHERE booking_id = ?",
                    (datetime.now().isoformat(), booking_id))
        _recalc_payment_status(cur, booking_id)
        cur.execute(
            "INSERT INTO booking_status_history (booking_id, previous_status, new_status, notes, changed_at) "
            "VALUES (?, 'Pending', 'Cancelled', ?, ?)",
            (booking_id, "Cancelled by customer" + (" Refunded \u20b1 {:.2f}.".format(settled) if settled > 0 else ""),
             datetime.now().isoformat()))
        conn.commit()
        return True, "Booking cancelled."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


VALID_TRANSITIONS = {
    "Pending": ["Confirmed", "Rejected", "Cancelled"],
    "Confirmed": ["Completed", "Cancelled"],
}


def update_booking_status(booking_id, new_status, admin_id, notes):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute("SELECT booking_status FROM bookings WHERE booking_id = ?", (booking_id,))
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return False, "Booking not found."
        old_status = row["booking_status"]
        allowed = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            conn.rollback()
            return False, "Cannot change status from {} to {}.".format(old_status, new_status)

        # A booking can only be completed once its payment is fully settled.
        if new_status == "Completed":
            cur.execute("SELECT payment_status, total_price FROM bookings WHERE booking_id = ?",
                        (booking_id,))
            pay = cur.fetchone()
            if pay and pay["payment_status"] != "Paid":
                conn.rollback()
                return False, ("Cannot complete: the booking is not fully paid "
                               "(payment status: {}). Record the payment first.".format(
                                   pay["payment_status"] or "Pending"))

        # Recheck availability on Confirm to prevent double booking
        if new_status == "Confirmed":
            cur.execute(
                "SELECT artist_id, appointment_date, start_time, end_time FROM bookings WHERE booking_id = ?", (booking_id,))
            b = cur.fetchone()
            if not is_slot_available(b["artist_id"], b["appointment_date"], b["start_time"], b["end_time"],
                                     exclude_booking_id=booking_id):
                conn.rollback()
                return False, "Cannot confirm: the appointment slot conflicts with another booking."

        # Cancelling or rejecting a paid booking refunds the recorded payments.
        refund_note = ""
        if new_status in ("Cancelled", "Rejected"):
            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments "
                        "WHERE booking_id = ? AND payment_status = 'Paid'", (booking_id,))
            settled = float(cur.fetchone()[0] or 0)
            if settled > 0:
                cur.execute("UPDATE payments SET payment_status = 'Refunded' "
                            "WHERE booking_id = ? AND payment_status = 'Paid'", (booking_id,))
                refund_note = " Refunded \u20b1 {:.2f}.".format(settled)

        cur.execute("UPDATE bookings SET booking_status = ?, updated_at = ? WHERE booking_id = ?",
                    (new_status, datetime.now().isoformat(), booking_id))
        _recalc_payment_status(cur, booking_id)
        cur.execute(
            "INSERT INTO booking_status_history (booking_id, previous_status, new_status, changed_by_admin_id, notes, changed_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (booking_id, old_status, new_status, admin_id, (notes or "") + refund_note,
             datetime.now().isoformat()))
        conn.commit()
        return True, "Status updated to {}.".format(new_status)
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_booking_notes(booking_id, notes):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE bookings SET admin_notes = ?, updated_at = ? WHERE booking_id = ?",
                    (notes, datetime.now().isoformat(), booking_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_status_history(booking_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT h.*, a.full_name AS admin_name FROM booking_status_history h "
            "LEFT JOIN admins a ON h.changed_by_admin_id = a.admin_id "
            "WHERE h.booking_id = ? ORDER BY h.changed_at DESC", (booking_id,))
        return cur.fetchall()
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# Payments
# ----------------------------------------------------------------------------
def get_payments():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT p.*, b.booking_reference, u.first_name || COALESCE(' ' || u.middle_name, '') || ' ' || u.last_name AS customer_name FROM payments p "
            "LEFT JOIN bookings b ON p.booking_id = b.booking_id "
            "LEFT JOIN users u ON b.user_id = u.user_id ORDER BY p.created_at DESC")
        return cur.fetchall()
    finally:
        conn.close()


def get_payments_for_booking(booking_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM payments WHERE booking_id = ? ORDER BY created_at DESC",
                    (booking_id,))
        return cur.fetchall()
    finally:
        conn.close()


def get_booking_full(booking_id):
    """A booking joined with its customer, design and artist for detail views."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT b.*, "
            "u.first_name || COALESCE(' ' || u.middle_name, '') || ' ' || u.last_name AS customer_name, "
            "u.email AS customer_email, u.phone AS customer_phone, "
            "p.package_name, p.category AS package_category, p.kind AS package_kind, "
            "a.full_name AS artist_name "
            "FROM bookings b "
            "LEFT JOIN users u ON b.user_id = u.user_id "
            "LEFT JOIN packages p ON b.package_id = p.package_id "
            "LEFT JOIN artists a ON b.artist_id = a.artist_id "
            "WHERE b.booking_id = ?", (booking_id,))
        return cur.fetchone()
    finally:
        conn.close()


def _recalc_payment_status(cur, booking_id):
    """Keep ``bookings.payment_status`` in sync with the payment records.

    The booking status is derived: fully settled -> Paid, anything refunded
    -> Refunded, otherwise -> Pending. Returns the resolved status.
    """
    cur.execute("SELECT total_price FROM bookings WHERE booking_id = ?", (booking_id,))
    row = cur.fetchone()
    if not row:
        return None
    total = float(row["total_price"] or 0)
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments "
                "WHERE booking_id = ? AND payment_status = 'Paid'", (booking_id,))
    paid = float(cur.fetchone()[0] or 0)
    cur.execute("SELECT COUNT(*) FROM payments WHERE booking_id = ?", (booking_id,))
    total_rows = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM payments WHERE booking_id = ? AND payment_status = 'Refunded'",
                (booking_id,))
    refunded = cur.fetchone()[0]

    if paid >= total and total > 0:
        status = "Paid"
    elif refunded and refunded == total_rows:
        status = "Refunded"
    else:
        status = "Pending"
    cur.execute("UPDATE bookings SET payment_status = ?, updated_at = ? WHERE booking_id = ?",
                (status, datetime.now().isoformat(), booking_id))
    return status


def record_payment(booking_id, amount, method, reference, status):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute(
            "INSERT INTO payments (booking_id, amount, payment_method, payment_reference, payment_status, paid_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (booking_id, amount, method, reference, status,
             datetime.now().isoformat() if status == "Paid" else None,
             datetime.now().isoformat()))
        payment_id = cur.lastrowid
        _recalc_payment_status(cur, booking_id)
        conn.commit()
        return payment_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# Dashboard statistics
# ----------------------------------------------------------------------------
def get_dashboard_stats():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        total_customers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM bookings")
        total_bookings = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM bookings WHERE appointment_date >= date('now') AND booking_status != 'Cancelled'")
        upcoming = cur.fetchone()[0]
        cur.execute("SELECT booking_status, COUNT(*) FROM bookings GROUP BY booking_status")
        status_counts = {r[0]: r[1] for r in cur.fetchall()}
        cur.execute(
            "SELECT p.package_name, COUNT(b.booking_id) AS cnt FROM packages p "
            "LEFT JOIN bookings b ON b.package_id = p.package_id GROUP BY p.package_id ORDER BY cnt DESC LIMIT 5")
        popular = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM artists WHERE is_active = 1")
        total_artists = cur.fetchone()[0]
        return {
            "total_customers": total_customers,
            "total_bookings": total_bookings,
            "upcoming": upcoming,
            "total_artists": total_artists,
            "status_counts": status_counts,
            "popular": popular,
        }
    finally:
        conn.close()


def get_recent_bookings(limit=10):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT b.*, u.first_name || COALESCE(' ' || u.middle_name, '') || ' ' || u.last_name AS customer_name, p.package_name, a.full_name AS artist_name FROM bookings b "
            "LEFT JOIN users u ON b.user_id = u.user_id "
            "LEFT JOIN packages p ON b.package_id = p.package_id "
            "LEFT JOIN artists a ON b.artist_id = a.artist_id "
            "ORDER BY b.created_at DESC LIMIT ?", (limit,))
        return cur.fetchall()
    finally:
        conn.close()


def get_customers():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, first_name, middle_name, last_name, email, phone, is_active FROM users "
            "WHERE is_active = 1 ORDER BY last_name, first_name")
        return cur.fetchall()
    finally:
        conn.close()
