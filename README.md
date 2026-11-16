# Tattoo Service Booking System

A complete desktop tattoo studio booking application built with **Python**, **Tkinter**, and **SQLite**.
Features a minimalist dark black-and-red interface inspired by modern booking apps.

## Project Structure

```
TattooBookingSystem/
├── main.py            # Application entry point and navigation
├── database.py        # Database connection, initialization, queries
├── auth.py            # Customer registration/login, admin authentication
├── booking.py         # Availability, booking, cancellation, status logic
├── customer.py        # Customer pages (browse, book, history, profile)
├── admin.py           # Admin dashboard and management screens
├── database.sql       # Complete SQL schema
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── assets/
    ├── package_images/     # Tattoo package images
    ├── artist_images/      # Artist profile images
    └── customer_references/# Customer-uploaded reference images
```

## Features

- Customer registration & login (email or phone) with secure password hashing
- Secure first-run admin account setup (no hardcoded default password)
- Browse, search, and filter tattoo packages
- Artist selection, date picker, and available time slots
- Tattoo placement dropdown (with custom "Other" option)
- Add-on services and price breakdown
- Booking creation with unique reference, overlap prevention, and status history
- Booking history and cancellation
- Admin dashboard with statistics, package/artist/addon CRUD, booking & payment management
- Dark black-and-red theme with Pillow image handling

## Installation

1. **Clone or download** this folder.
2. **Install Python 3** (3.8 or newer).
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application:**
   ```bash
   python main.py
   ```

The database (`tattoo_booking.db`) and sample data are created automatically on first run.

## First-Run Admin Setup

A default administrator account is created automatically on first launch:

- **Username:** `admin`
- **Password:** `admin123`

**Change these credentials after your first login.** No default customer account exists — customers register themselves through the login screen.

### Hidden Admin Login (Easter Egg)

On the login screen, click the "Tattoo Studio" title **5 times** (or click the subtle "Admin access?" link) to switch the login form to admin mode. Then sign in with the admin credentials above.

## Testing Workflows

- Register a customer account, then log in.
- Browse packages, select **Book Now**, pick an artist/date/time, and complete a booking.
- Log in as admin to confirm/reject/cancel bookings and manage packages.
- Try booking the same artist/date/time slot twice to verify overlap prevention.

## Notes

- No real payment gateway is integrated. Payments are managed manually by the admin.
- Images are stored as files; only relative paths are saved in SQLite.
- Deactivated packages/artists keep their historical booking records intact.
