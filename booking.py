from database import (
    get_active_packages, get_package, get_categories, search_packages,
    get_active_artists, get_artist, get_addons, get_availability,
    is_slot_available, add_minutes, create_booking as db_create_booking,
    get_booking, get_bookings_by_user, cancel_booking as db_cancel_booking,
    get_booking_addons,
)

PLACEMENT_OPTIONS = [
    "Forearm", "Inner Forearm", "Upper Arm", "Bicep", "Wrist", "Hand", "Fingers",
    "Shoulder", "Collarbone", "Chest", "Sternum", "Ribs", "Upper Back", "Lower Back",
    "Spine", "Neck", "Behind the Ear", "Nape", "Thigh", "Knee", "Calf", "Shin",
    "Ankle", "Foot", "Toes", "Hip", "Waist", "Abdomen", "Other",
]

SIZE_OPTIONS = ["Small", "Medium", "Large", "Extra Large"]


def get_placement_options():
    return PLACEMENT_OPTIONS


def get_size_options():
    return SIZE_OPTIONS


def create_booking_flight(user_id, package_id, artist_id, appointment_date, start_time,
                          placement, tattoo_size, design_description, reference_image_path,
                          customer_notes, addon_selections):
    """High-level wrapper around the database booking creation."""
    return db_create_booking(
        user_id, package_id, artist_id, appointment_date, start_time,
        placement, tattoo_size, design_description, reference_image_path,
        customer_notes, addon_selections or [])


def booking_details(booking_id):
    b = get_booking(booking_id)
    if not b:
        return None
    addons = get_booking_addons(booking_id)
    return dict(b), addons


def cancel_my_booking(booking_id, user_id):
    return db_cancel_booking(booking_id, user_id)
