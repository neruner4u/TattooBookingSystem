-- ============================================================================
-- Tattoo Service Booking System
-- SQLite Database Schema
-- ============================================================================
PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Users (customers)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    middle_name     TEXT,
    last_name       TEXT    NOT NULL,
    email           TEXT    UNIQUE,
    phone           TEXT    UNIQUE,
    password_hash   TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

-- ----------------------------------------------------------------------------
-- Admins
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    admin_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT    NOT NULL,
    username        TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- ----------------------------------------------------------------------------
-- Tattoo packages
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS packages (
    package_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    package_name    TEXT    NOT NULL,
    description     TEXT,
    category        TEXT    NOT NULL,
    kind            TEXT    NOT NULL DEFAULT 'Package' CHECK (kind IN ('Package', 'Tattoo')),
    price           REAL    NOT NULL CHECK (price >= 0),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    image_path      TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- Artists
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artists (
    artist_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT    NOT NULL,
    bio             TEXT,
    specialties     TEXT,
    profile_image   TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- Artist availability (daily working windows)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artist_availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id       INTEGER NOT NULL,
    available_date  TEXT    NOT NULL,
    start_time      TEXT    NOT NULL,
    end_time        TEXT    NOT NULL,
    is_available    INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE,
    UNIQUE (artist_id, available_date, start_time),
    CHECK (time(start_time) < time(end_time))
);

-- ----------------------------------------------------------------------------
-- Bookings
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    booking_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_reference   TEXT    NOT NULL UNIQUE,
    user_id             INTEGER NOT NULL,
    package_id          INTEGER NOT NULL,
    artist_id           INTEGER NOT NULL,
    appointment_date    TEXT    NOT NULL,
    start_time          TEXT    NOT NULL,
    end_time            TEXT    NOT NULL,
    placement           TEXT    NOT NULL,
    tattoo_size         TEXT    NOT NULL,
    design_description  TEXT,
    reference_image_path TEXT,
    base_price          REAL    NOT NULL CHECK (base_price >= 0),
    additional_cost     REAL    NOT NULL CHECK (additional_cost >= 0),
    total_price         REAL    NOT NULL CHECK (total_price >= 0),
    booking_status      TEXT    NOT NULL CHECK (booking_status IN ('Pending','Confirmed','Completed','Cancelled','Rejected')),
    payment_status      TEXT    NOT NULL DEFAULT 'Pending' CHECK (payment_status IN ('Pending','Paid','Failed','Refunded')),
    customer_notes      TEXT,
    admin_notes         TEXT,
    created_at          TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)      REFERENCES users(user_id),
    FOREIGN KEY (package_id)   REFERENCES packages(package_id),
    FOREIGN KEY (artist_id)    REFERENCES artists(artist_id),
    CHECK (time(start_time) < time(end_time))
);

-- ----------------------------------------------------------------------------
-- Booking status history
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS booking_status_history (
    history_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id         INTEGER NOT NULL,
    previous_status    TEXT,
    new_status         TEXT    NOT NULL,
    changed_by_admin_id INTEGER,
    notes              TEXT,
    changed_at         TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id)          REFERENCES bookings(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_admin_id) REFERENCES admins(admin_id)
);

-- ----------------------------------------------------------------------------
-- Package add-ons
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS package_addons (
    addon_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    addon_name    TEXT    NOT NULL,
    description   TEXT,
    price         REAL    NOT NULL CHECK (price >= 0),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- ----------------------------------------------------------------------------
-- Booking add-ons
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS booking_addons (
    booking_addon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id       INTEGER NOT NULL,
    addon_id         INTEGER NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price       REAL    NOT NULL CHECK (unit_price >= 0),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (addon_id)   REFERENCES package_addons(addon_id)
);

-- ----------------------------------------------------------------------------
-- Payments (managed manually by admin; no real payment gateway)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id         INTEGER NOT NULL,
    amount             REAL    NOT NULL CHECK (amount >= 0),
    payment_method     TEXT,
    payment_reference  TEXT,
    payment_status     TEXT    NOT NULL DEFAULT 'Pending' CHECK (payment_status IN ('Pending','Paid','Failed','Refunded')),
    paid_at            TEXT,
    created_at         TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);

-- ----------------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_email      ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone      ON users(phone);
CREATE INDEX IF NOT EXISTS idx_admins_username  ON admins(username);
CREATE INDEX IF NOT EXISTS idx_packages_category ON packages(category);
CREATE INDEX IF NOT EXISTS idx_packages_active  ON packages(is_active);
CREATE INDEX IF NOT EXISTS idx_artists_active   ON artists(is_active);
CREATE INDEX IF NOT EXISTS idx_availability_artist_date ON artist_availability(artist_id, available_date);
CREATE INDEX IF NOT EXISTS idx_bookings_user    ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_artist_date ON bookings(artist_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_bookings_status  ON bookings(booking_status);
CREATE INDEX IF NOT EXISTS idx_bookings_reference ON bookings(booking_reference);
CREATE INDEX IF NOT EXISTS idx_booking_addons_booking ON booking_addons(booking_id);
CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id);
