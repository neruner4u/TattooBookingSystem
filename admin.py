"""Admin-facing screens — dashboard and management modules.

Every screen renders inside ``app.content_frame`` (the shell in main.py) and
reuses the shared widgets from ``components`` so the whole application shares
one visual language.
"""
from datetime import datetime
import os
import shutil
import uuid
from tkinter import filedialog

import customtkinter as ctk

import theme as T
import components as C
from database import (
    PKG_IMG_DIR, ARTIST_IMG_DIR,
    get_all_packages_admin, get_package, add_package, update_package, deactivate_package,
    get_all_artists_admin, get_artist, add_artist, update_artist, deactivate_artist,
    add_availability,
    get_all_addons_admin, add_addon, deactivate_addon,
    get_all_bookings_admin, get_booking_full, get_booking_addons, get_payments_for_booking,
    update_booking_status, update_booking_notes, get_status_history, VALID_TRANSITIONS,
    get_payments, record_payment, get_customers, get_dashboard_stats, get_recent_bookings,
    time_to_minutes, get_connection,
)

BOOKING_STATUSES = ["Pending", "Confirmed", "Completed", "Cancelled", "Rejected"]
PAYMENT_STATUSES = ["Pending", "Paid", "Failed", "Refunded"]
BOOKING_STATUS_COLORS = {
    "Pending": T.WARNING, "Confirmed": T.INFO, "Completed": T.SUCCESS,
    "Cancelled": T.TEXT_MUTED, "Rejected": T.RED,
}
PAYMENT_STATUS_COLORS = {
    "Pending": T.WARNING, "Paid": T.SUCCESS, "Failed": T.RED, "Refunded": T.TEXT_MUTED,
}
IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp")]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _begin(app, nav_key):
    app.clear_content()
    try:
        app.set_active_nav(nav_key)
    except Exception:
        pass


def _set_title(app, title, subtitle=""):
    try:
        app.top_title.configure(text=title)
        app.top_subtitle.configure(text=subtitle)
    except Exception:
        pass


def _page(app):
    """A transparent container that fills the content area."""
    frame = ctk.CTkFrame(app.content_frame, fg_color="transparent")
    frame.pack(fill="both", expand=True)
    return frame


def _money(value):
    try:
        return "₱ {:.2f}".format(float(value or 0))
    except (TypeError, ValueError):
        return "₱ 0.00"


def _detail_row(parent, label, value):
    """A stacked label/value pair used by the read-only detail dialogs."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=(0, T.S3))
    ctk.CTkLabel(row, text=label.upper(), font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w")
    ctk.CTkLabel(row, text=str(value) if value not in (None, "") else "—",
                 font=T.F_BODY, text_color=T.TEXT, anchor="w", justify="left",
                 wraplength=420).pack(anchor="w", pady=(2, 0))
    return row


def _search_filter(values, term):
    if not term:
        return True
    haystack = " ".join(str(v) for v in values).lower()
    return term in haystack


def save_asset(src_path, folder):
    """Copy a picked file into the project asset folder and return its path."""
    os.makedirs(folder, exist_ok=True)
    ext = os.path.splitext(src_path)[1]
    name = "asset_{}{}".format(uuid.uuid4().hex[:8], ext.lower())
    dst = os.path.join(folder, name)
    shutil.copy2(src_path, dst)
    return dst.replace("\\", "/")


def _image_picker(parent, folder, initial, size=(260, 200)):
    """Image preview + import button. Returns a dict with the current path."""
    state = {"path": initial}
    holder = ctk.CTkFrame(parent, fg_color=T.CARD, corner_radius=T.RADIUS,
                          width=size[0], height=size[1])
    holder.pack()
    holder.pack_propagate(False)

    def refresh():
        for widget in holder.winfo_children():
            widget.destroy()
        C.image_label(holder, state["path"], size, radius=T.RADIUS,
                      fallback="No image").pack()

    def import_img():
        picked = filedialog.askopenfilename(title="Select image",
                                            filetypes=IMAGE_FILETYPES)
        if picked:
            state["path"] = save_asset(picked, folder)
            refresh()

    refresh()
    C.mk_button(parent, "Import / replace image", import_img, kind="secondary",
                icon=C.G_UPLOAD, width=size[0], height=40).pack(pady=(T.S3, 0))
    return state


def _dialog(app, title, width, height, icon=C.G_PEN):
    dlg = ctk.CTkToplevel(app.root)
    dlg.title(title)
    dlg.configure(fg_color=T.BG)
    dlg.resizable(False, False)
    dlg.transient(app.root)
    C._center(dlg, app.root, width, height)

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=T.S6, pady=T.S5)

    head = ctk.CTkFrame(body, fg_color="transparent")
    head.pack(fill="x", pady=(0, T.S5))
    C.icon_label(head, icon, color=T.RED).pack(side="left")
    ctk.CTkLabel(head, text=title, font=T.F_H1, text_color=T.TEXT,
                 anchor="w").pack(side="left", padx=(T.S3, 0))

    dlg.after(60, lambda: dlg.grab_set())
    dlg.after(80, dlg.lift)
    return dlg, body


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def build_dashboard(app):
    _begin(app, "dashboard")
    _set_title(app, "Dashboard", "Studio performance at a glance")
    scroll = C.scroll_area(app.content_frame)
    scroll.pack(fill="both", expand=True)

    stats = get_dashboard_stats()

    cards = [
        (C.G_USER, "Total customers", stats["total_customers"], T.RED),
        (C.G_CAL, "Total bookings", stats["total_bookings"], T.INFO),
        (C.G_CLOCK, "Upcoming", stats["upcoming"], T.GOLD),
        (C.G_STAR, "Active artists", stats["total_artists"], T.SUCCESS),
    ]
    row = ctk.CTkFrame(scroll, fg_color="transparent")
    row.pack(fill="x", pady=(0, T.S5))
    for i, (glyph, label, value, accent) in enumerate(cards):
        row.grid_columnconfigure(i, weight=1, uniform="dstat")
        C.stat_card(row, glyph, label, value, accent=accent).grid(
            row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))

    # -- bookings by status
    C.section_title(scroll, "Bookings by status")
    srow = ctk.CTkFrame(scroll, fg_color="transparent")
    srow.pack(fill="x", pady=(0, T.S5))
    for i, status in enumerate(BOOKING_STATUSES):
        srow.grid_columnconfigure(i, weight=1, uniform="sstat")
        card = C.card(srow)
        card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=T.S4, pady=T.S4)
        C.status_badge(inner, status).pack(anchor="w")
        ctk.CTkLabel(inner, text=str(stats["status_counts"].get(status, 0)),
                     font=(T.FAMILY, 22, "bold"), text_color=T.TEXT,
                     anchor="w").pack(anchor="w", pady=(T.S2, 0))

    # -- recent bookings
    header = ctk.CTkFrame(scroll, fg_color="transparent")
    header.pack(fill="x", pady=(0, T.S3))
    ctk.CTkLabel(header, text="Recent bookings", font=T.F_H2, text_color=T.TEXT,
                 anchor="w").pack(side="left")
    C.mk_button(header, "Manage bookings", lambda: build_booking_manager(app),
                kind="ghost", width=160, height=32).pack(side="right")

    table = C.DataTable(scroll, [
        ("reference", "Reference", 180, "w"),
        ("customer", "Customer", 200, "w"),
        ("package", "Package", 220, "w"),
        ("date", "Date", 120, "w"),
        ("status", "Status", 130, "w"),
    ], height=7)
    table.pack(fill="x")
    recent = list(get_recent_bookings(7) or [])
    if recent:
        table.set_rows([((
            b["booking_reference"], b["customer_name"] or "-", b["package_name"] or "-",
            b["appointment_date"], b["booking_status"],
        ), None) for b in recent])
    else:
        table.set_rows([])

    # -- most booked packages
    C.section_title(scroll, "Most booked packages", pady=(T.S6, T.S3))
    popular = list(stats["popular"] or [])
    if not popular:
        C.empty_state(scroll, "no_gallery.png", "No package data yet",
                      "Bookings per package will appear here once customers book.")
    else:
        prow = ctk.CTkFrame(scroll, fg_color="transparent")
        prow.pack(fill="x")
        for i, p in enumerate(popular):
            prow.grid_columnconfigure(i, weight=1, uniform="pop")
            card = C.card(prow)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=T.S4, pady=T.S4)
            ctk.CTkLabel(inner, text=p["package_name"], font=T.F_SMALL_B,
                         text_color=T.TEXT, anchor="w", wraplength=180).pack(anchor="w")
            ctk.CTkLabel(inner, text="{} booking{}".format(p["cnt"], "" if p["cnt"] == 1 else "s"),
                         font=T.F_TINY, text_color=T.RED, anchor="w").pack(anchor="w",
                                                                          pady=(4, 0))


# ---------------------------------------------------------------------------
# Package manager
# ---------------------------------------------------------------------------
def build_package_manager(app, kind="Package"):
    is_tattoo = kind == "Tattoo"
    nav_key = "tattoos" if is_tattoo else "packages"
    noun = "tattoos" if is_tattoo else "packages"
    singular = "tattoo" if is_tattoo else "package"
    item_label = "Tattoo" if is_tattoo else "Package"

    _begin(app, nav_key)
    _set_title(app, "Individual tattoos" if is_tattoo else "Packages",
               "Create and manage bookable single tattoos" if is_tattoo
               else "Create and manage your tattoo packages")
    wrap = _page(app)

    actions = C.page_header(wrap, "{} management".format(item_label),
                            "Add new designs, update pricing and import artwork")
    C.primary_button(actions, "Add {}".format(singular),
                     lambda: open_package_dialog(app, kind=kind),
                     icon=C.G_PLUS, width=170, height=42).pack(side="right")
    C.mk_button(actions, "Refresh", lambda: build_package_manager(app, kind=kind),
                kind="secondary", icon=C.G_REFRESH, width=120, height=42).pack(
        side="right", padx=(0, T.S3))

    bar = C.card(wrap)
    bar.pack(fill="x", pady=(0, T.S4))
    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)
    search_wrap, ent = C.search_entry(inner, "Search {}…".format(noun), width=300)
    search_wrap.pack(side="left")
    count_lbl = ctk.CTkLabel(inner, text="", font=T.F_SMALL, text_color=T.TEXT_MUTED)
    count_lbl.pack(side="right")

    table = C.DataTable(wrap, [
        ("id", "ID", 60, "center"),
        ("name", item_label, 250, "w"),
        ("category", "Category", 160, "w"),
        ("price", "Price", 110, "e"),
        ("duration", "Duration", 110, "center"),
        ("active", "Active", 90, "center"),
        ("image", "Artwork", 220, "w"),
    ], height=15)
    table.pack(fill="both", expand=True)

    state = {"term": ""}

    def load():
        rows = []
        term = state["term"].lower()
        for p in get_all_packages_admin(kind):
            vals = (p["package_id"], p["package_name"], p["category"],
                    _money(p["price"]), "{} min".format(p["duration_minutes"]),
                    "Yes" if p["is_active"] else "No",
                    os.path.basename(p["image_path"]) if p["image_path"] else "—")
            if not _search_filter(vals, term):
                continue
            rows.append((vals, None))
        table.set_rows(rows)
        count_lbl.configure(text="{} {}{}".format(len(rows), singular,
                                                  "" if len(rows) == 1 else "s"))

    def on_search(_=None):
        state["term"] = ent.get().strip()
        load()

    ent.bind("<KeyRelease>", on_search)
    if not get_all_packages_admin(kind):
        C.toast(app, "No {} found.".format(noun), "info")

    load()

    def selected_id():
        vals = table.selected_values()
        if not vals:
            C.toast(app, "Select a {} first.".format(singular), "warning")
            return None
        return int(vals[0])

    def edit_selected():
        pid = selected_id()
        if pid is not None:
            open_package_dialog(app, package_id=pid, kind=kind)

    def view_details():
        pid = selected_id()
        if pid is not None:
            open_package_details(app, pid)

    table.tree.bind("<Double-1>", lambda _e: view_details())

    def deactivate_selected():
        pid = selected_id()
        if pid is None:
            return
        vals = table.selected_values()
        name = vals[1]

        def do_it():
            deactivate_package(pid)
            load()
            C.toast(app, "{} deactivated.".format(item_label), "success")

        C.confirm_dialog(app, "Deactivate {}".format(singular),
                         "Deactivate '{}'? Existing bookings are preserved and the "
                         "{} is hidden from customers.".format(name, singular),
                         do_it, confirm_text="Deactivate", kind="danger")

    def import_image():
        pid = selected_id()
        if pid is None:
            return
        pkg = get_package(pid)
        picked = filedialog.askopenfilename(title="Select image",
                                            filetypes=IMAGE_FILETYPES)
        if not picked:
            return
        path = save_asset(picked, PKG_IMG_DIR)
        update_package(pid, pkg["package_name"], pkg["description"], pkg["category"],
                       pkg["price"], pkg["duration_minutes"], path)
        load()
        C.toast(app, "Artwork imported.", "success")

    btns = ctk.CTkFrame(wrap, fg_color="transparent")
    btns.pack(fill="x", pady=(T.S4, 0))
    C.mk_button(btns, "View details", view_details, kind="secondary", icon=C.G_IMAGE,
                width=150, height=42).pack(side="left")
    C.mk_button(btns, "Edit selected", edit_selected, kind="secondary", icon=C.G_PEN,
                width=160, height=42).pack(side="left", padx=(T.S3, 0))
    C.mk_button(btns, "Import artwork", import_image, kind="secondary",
                icon=C.G_UPLOAD, width=170, height=42).pack(side="left", padx=(T.S3, 0))
    C.mk_button(btns, "Deactivate", deactivate_selected, kind="danger", icon=C.G_TRASH,
                width=140, height=42).pack(side="left", padx=(T.S3, 0))


def build_tattoo_manager(app):
    build_package_manager(app, kind="Tattoo")


def open_package_dialog(app, package_id=None, kind="Package"):
    is_edit = package_id is not None
    is_tattoo = kind == "Tattoo"
    singular = "tattoo" if is_tattoo else "package"
    item_label = "Tattoo" if is_tattoo else "Package"
    pkg = get_package(package_id) if is_edit else None

    dlg, body = _dialog(app, "{} {}".format("Edit" if is_edit else "Add", singular),
                        780, 620, icon=C.G_IMAGE)

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True)
    left = ctk.CTkFrame(cols, fg_color="transparent")
    left.pack(side="left", fill="both", expand=True, padx=(0, T.S5))
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.pack(side="right", fill="y")

    f_name, e_name = C.labeled_entry(left, "{} name *".format(item_label),
                                     "e.g. Japanese Koi Sleeve" if not is_tattoo
                                     else "e.g. Japanese Koi — Single Tattoo")
    f_name.pack(fill="x", pady=(0, T.S3))
    f_cat, e_cat = C.labeled_entry(left, "Category *", "e.g. Japanese")
    f_cat.pack(fill="x", pady=(0, T.S3))

    prow = ctk.CTkFrame(left, fg_color="transparent")
    prow.pack(fill="x", pady=(0, T.S3))
    f_price, e_price = C.labeled_entry(prow, "Price *", "0.00")
    f_price.pack(side="left", fill="x", expand=True, padx=(0, T.S3))
    f_dur, e_dur = C.labeled_entry(prow, "Duration (min) *", "60")
    f_dur.pack(side="left", fill="x", expand=True)

    C.field_label(left, "Description").pack(anchor="w")
    txt_desc = C.text_area(left, height=120)
    txt_desc.pack(fill="x")

    C.field_label(right, "Artwork").pack(anchor="w", pady=(0, 6))
    image = _image_picker(right, PKG_IMG_DIR, pkg["image_path"] if is_edit else None,
                          size=(270, 200))

    if is_edit:
        e_name.insert(0, pkg["package_name"] or "")
        e_cat.insert(0, pkg["category"] or "")
        e_price.insert(0, "{:.2f}".format(float(pkg["price"])))
        e_dur.insert(0, str(pkg["duration_minutes"]))
        txt_desc.insert("1.0", pkg["description"] or "")

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=(T.S5, 0))

    def save():
        name = e_name.get().strip()
        category = e_cat.get().strip()
        try:
            price = float(e_price.get())
            duration = int(e_dur.get())
        except ValueError:
            C.alert_dialog(app, "Invalid input", "Price and duration must be numbers.",
                           "error")
            return
        if not name or not category or price < 0 or duration <= 0:
            C.alert_dialog(app, "Invalid input",
                           "Please fill all required fields correctly.", "error")
            return
        description = txt_desc.get("1.0", "end-1c").strip()
        if is_edit:
            update_package(package_id, name, description, category, price, duration,
                           image["path"] or None)
        else:
            add_package(name, description, category, price, duration, image["path"] or None,
                        kind=kind)
        dlg.destroy()
        C.toast(app, "{} {}.".format(item_label,
                                     "updated" if is_edit else "created"), "success")
        build_package_manager(app, kind=kind)

    C.mk_button(footer, "Cancel", dlg.destroy, kind="secondary", width=130,
                height=42).pack(side="right")
    C.primary_button(footer, "Save {}".format(singular), save, width=180,
                     height=42).pack(side="right", padx=(0, T.S3))


def open_package_details(app, package_id):
    """Read-only, in-depth view of a package or tattoo straight from the database."""
    pkg = get_package(package_id)
    if not pkg:
        C.toast(app, "Item not found.", "error")
        return

    is_tattoo = pkg["kind"] == "Tattoo"
    singular = "tattoo" if is_tattoo else "package"

    conn = get_connection()
    try:
        stats = conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN booking_status = 'Completed' THEN 1 ELSE 0 END) AS completed, "
            "COALESCE(SUM(CASE WHEN booking_status IN ('Confirmed','Completed') "
            "THEN total_price ELSE 0 END), 0) AS revenue, "
            "MAX(appointment_date) AS last_booking "
            "FROM bookings WHERE package_id = ?", (package_id,)).fetchone()
    finally:
        conn.close()

    dlg, body = _dialog(app, "{} details".format("Tattoo" if is_tattoo else "Package"),
                        900, 660, icon=C.G_IMAGE)

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True)

    left = ctk.CTkFrame(cols, fg_color="transparent", width=340)
    left.pack(side="left", fill="y", padx=(0, T.S5))
    left.pack_propagate(False)
    C.image_label(left, pkg["image_path"], (340, 280), radius=T.RADIUS_LG,
                  fallback="No artwork uploaded").pack()
    ctk.CTkLabel(left, text="Artwork on file", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(T.S3, 0))
    ctk.CTkLabel(left, text=os.path.basename(pkg["image_path"]) if pkg["image_path"]
                 else "None", font=T.F_SMALL, text_color=T.TEXT_SEC,
                 anchor="w", wraplength=330, justify="left").pack(anchor="w", pady=(2, 0))

    right = C.scroll_area(cols)
    right.pack(side="right", fill="both", expand=True)

    ctk.CTkLabel(right, text=pkg["package_name"], font=T.F_H2, text_color=T.TEXT,
                 anchor="w", justify="left", wraplength=460).pack(anchor="w")

    tags = ctk.CTkFrame(right, fg_color="transparent")
    tags.pack(anchor="w", pady=(T.S3, T.S4))
    C.badge(tags, "Single tattoo" if is_tattoo else "Package").pack(side="left")
    C.badge(tags, pkg["category"]).pack(side="left", padx=(T.S2, 0))
    C.badge(tags, "Active" if pkg["is_active"] else "Inactive",
            color=T.SUCCESS if pkg["is_active"] else T.TEXT_MUTED).pack(
        side="left", padx=(T.S2, 0))

    facts = ctk.CTkFrame(right, fg_color="transparent")
    facts.pack(fill="x")
    for label, value in [
        ("Price", _money(pkg["price"])),
        ("Duration", "{} minutes".format(pkg["duration_minutes"])),
        ("Category", pkg["category"]),
        ("Total bookings", stats["total"] or 0),
        ("Completed bookings", stats["completed"] or 0),
        ("Confirmed / completed revenue", _money(stats["revenue"])),
        ("Last appointment", stats["last_booking"] or "—"),
    ]:
        _detail_row(facts, label, value)

    C.divider(right, pady=(T.S2, T.S3))
    _detail_row(right, "Description", pkg["description"] or "No description provided.")

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=(T.S5, 0))
    C.mk_button(footer, "Close", dlg.destroy, kind="secondary", width=130,
                height=42).pack(side="right")

    def edit():
        dlg.destroy()
        open_package_dialog(app, package_id=package_id, kind=pkg["kind"])

    C.primary_button(footer, "Edit {}".format(singular), edit, width=180,
                     height=42).pack(side="right", padx=(0, T.S3))


# ---------------------------------------------------------------------------
# Artist manager
# ---------------------------------------------------------------------------
def build_artist_manager(app):
    _begin(app, "artists")
    _set_title(app, "Artists", "Manage your resident tattoo artists")
    wrap = _page(app)

    actions = C.page_header(wrap, "Artist management",
                            "Profiles, specialities and availability roster")
    C.primary_button(actions, "Add artist", lambda: open_artist_dialog(app),
                     icon=C.G_PLUS, width=150, height=42).pack(side="right")
    C.mk_button(actions, "Refresh", lambda: build_artist_manager(app),
                kind="secondary", icon=C.G_REFRESH, width=120, height=42).pack(
        side="right", padx=(0, T.S3))

    bar = C.card(wrap)
    bar.pack(fill="x", pady=(0, T.S4))
    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)
    search_wrap, ent = C.search_entry(inner, "Search artists…", width=300)
    search_wrap.pack(side="left")
    count_lbl = ctk.CTkLabel(inner, text="", font=T.F_SMALL, text_color=T.TEXT_MUTED)
    count_lbl.pack(side="right")

    table = C.DataTable(wrap, [
        ("id", "ID", 60, "center"),
        ("name", "Artist", 240, "w"),
        ("specialties", "Specialities", 300, "w"),
        ("active", "Active", 90, "center"),
        ("image", "Portrait", 220, "w"),
    ], height=15)
    table.pack(fill="both", expand=True)

    state = {"term": ""}

    def load():
        rows = []
        term = state["term"].lower()
        for a in get_all_artists_admin():
            vals = (a["artist_id"], a["full_name"], a["specialties"] or "—",
                    "Yes" if a["is_active"] else "No",
                    os.path.basename(a["profile_image"]) if a["profile_image"] else "—")
            if not _search_filter(vals, term):
                continue
            rows.append((vals, None))
        table.set_rows(rows)
        count_lbl.configure(text="{} artist{}".format(len(rows),
                                                      "" if len(rows) == 1 else "s"))

    def on_search(_=None):
        state["term"] = ent.get().strip()
        load()

    ent.bind("<KeyRelease>", on_search)
    load()

    def selected_id():
        vals = table.selected_values()
        if not vals:
            C.toast(app, "Select an artist first.", "warning")
            return None
        return int(vals[0])

    def edit_selected():
        aid = selected_id()
        if aid is not None:
            open_artist_dialog(app, artist_id=aid)

    def view_details():
        aid = selected_id()
        if aid is not None:
            open_artist_details(app, aid)

    table.tree.bind("<Double-1>", lambda _e: view_details())

    def deactivate_selected():
        aid = selected_id()
        if aid is None:
            return
        name = table.selected_values()[1]

        def do_it():
            deactivate_artist(aid)
            load()
            C.toast(app, "Artist deactivated.", "success")

        C.confirm_dialog(app, "Deactivate artist",
                         "Deactivate '{}'? Existing bookings are preserved.".format(name),
                         do_it, confirm_text="Deactivate", kind="danger")

    btns = ctk.CTkFrame(wrap, fg_color="transparent")
    btns.pack(fill="x", pady=(T.S4, 0))
    C.mk_button(btns, "View details", view_details, kind="secondary", icon=C.G_USER,
                width=150, height=42).pack(side="left")
    C.mk_button(btns, "Edit selected", edit_selected, kind="secondary", icon=C.G_PEN,
                width=160, height=42).pack(side="left", padx=(T.S3, 0))
    C.mk_button(btns, "Deactivate", deactivate_selected, kind="danger", icon=C.G_TRASH,
                width=140, height=42).pack(side="left", padx=(T.S3, 0))


def open_artist_dialog(app, artist_id=None):
    is_edit = artist_id is not None
    art = get_artist(artist_id) if is_edit else None

    dlg, body = _dialog(app, "Edit artist" if is_edit else "Add artist",
                        760, 600, icon=C.G_STAR)

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True)
    left = ctk.CTkFrame(cols, fg_color="transparent")
    left.pack(side="left", fill="both", expand=True, padx=(0, T.S5))
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.pack(side="right", fill="y")

    f_name, e_name = C.labeled_entry(left, "Full name *", "e.g. Marco Rivera")
    f_name.pack(fill="x", pady=(0, T.S3))
    f_spec, e_spec = C.labeled_entry(left, "Specialities", "e.g. Japanese, Blackwork")
    f_spec.pack(fill="x", pady=(0, T.S3))

    C.field_label(left, "Biography").pack(anchor="w")
    txt_bio = C.text_area(left, height=150)
    txt_bio.pack(fill="x")

    C.field_label(right, "Portrait").pack(anchor="w", pady=(0, 6))
    image = _image_picker(right, ARTIST_IMG_DIR, art["profile_image"] if is_edit else None,
                          size=(240, 240))

    if is_edit:
        e_name.insert(0, art["full_name"] or "")
        e_spec.insert(0, art["specialties"] or "")
        txt_bio.insert("1.0", art["bio"] or "")

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=(T.S5, 0))

    def save():
        name = e_name.get().strip()
        if not name:
            C.alert_dialog(app, "Invalid input", "Full name is required.", "error")
            return
        specialties = e_spec.get().strip()
        bio = txt_bio.get("1.0", "end-1c").strip()
        if is_edit:
            update_artist(artist_id, name, bio, specialties, image["path"] or None)
        else:
            add_artist(name, bio, specialties, image["path"] or None)
        dlg.destroy()
        C.toast(app, "Artist {}.".format("updated" if is_edit else "created"), "success")
        build_artist_manager(app)

    C.mk_button(footer, "Cancel", dlg.destroy, kind="secondary", width=130,
                height=42).pack(side="right")
    C.primary_button(footer, "Save artist", save, width=180,
                     height=42).pack(side="right", padx=(0, T.S3))


def open_artist_details(app, artist_id):
    """Read-only, in-depth view of an artist straight from the database."""
    art = get_artist(artist_id)
    if not art:
        C.toast(app, "Artist not found.", "error")
        return

    conn = get_connection()
    try:
        stats = conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN booking_status = 'Completed' THEN 1 ELSE 0 END) AS completed, "
            "SUM(CASE WHEN appointment_date >= date('now') "
            "AND booking_status IN ('Pending','Confirmed') THEN 1 ELSE 0 END) AS upcoming, "
            "COALESCE(SUM(CASE WHEN booking_status IN ('Confirmed','Completed') "
            "THEN total_price ELSE 0 END), 0) AS revenue "
            "FROM bookings WHERE artist_id = ?", (artist_id,)).fetchone()
        slots = conn.execute(
            "SELECT available_date, start_time, end_time, is_available "
            "FROM artist_availability WHERE artist_id = ? "
            "ORDER BY available_date DESC, start_time", (artist_id,)).fetchall()
    finally:
        conn.close()

    dlg, body = _dialog(app, "Artist details", 900, 680, icon=C.G_STAR)

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True)

    left = ctk.CTkFrame(cols, fg_color="transparent", width=300)
    left.pack(side="left", fill="y", padx=(0, T.S5))
    left.pack_propagate(False)
    C.image_label(left, art["profile_image"], (300, 300), radius=T.RADIUS_LG,
                  fallback="No portrait uploaded").pack()
    ctk.CTkLabel(left, text="Portrait on file", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(T.S3, 0))
    ctk.CTkLabel(left, text=os.path.basename(art["profile_image"]) if art["profile_image"]
                 else "None", font=T.F_SMALL, text_color=T.TEXT_SEC,
                 anchor="w", wraplength=290, justify="left").pack(anchor="w", pady=(2, 0))

    right = C.scroll_area(cols)
    right.pack(side="right", fill="both", expand=True)

    ctk.CTkLabel(right, text=art["full_name"], font=T.F_H2, text_color=T.TEXT,
                 anchor="w", justify="left", wraplength=460).pack(anchor="w")

    tags = ctk.CTkFrame(right, fg_color="transparent")
    tags.pack(anchor="w", pady=(T.S3, T.S4))
    specs = [s.strip() for s in (art["specialties"] or "").split(",") if s.strip()]
    for spec in specs:
        C.badge(tags, spec).pack(side="left", padx=(0, T.S2))
    C.badge(tags, "Active" if art["is_active"] else "Inactive",
            color=T.SUCCESS if art["is_active"] else T.TEXT_MUTED).pack(side="left")

    facts = ctk.CTkFrame(right, fg_color="transparent")
    facts.pack(fill="x")
    for label, value in [
        ("Total bookings", stats["total"] or 0),
        ("Completed tattoos", stats["completed"] or 0),
        ("Upcoming appointments", stats["upcoming"] or 0),
        ("Confirmed / completed revenue", _money(stats["revenue"])),
        ("Availability slots on file", len(slots)),
    ]:
        _detail_row(facts, label, value)

    C.divider(right, pady=(T.S2, T.S3))
    _detail_row(right, "Biography", art["bio"] or "No biography provided.")

    C.divider(right, pady=(T.S2, T.S3))
    ctk.CTkLabel(right, text="AVAILABILITY", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(0, T.S2))
    if slots:
        for slot in slots:
            srow = ctk.CTkFrame(right, fg_color=T.ELEVATED, corner_radius=T.RADIUS)
            srow.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(srow, text="{}   {} – {}".format(
                slot["available_date"], slot["start_time"], slot["end_time"]),
                font=T.F_SMALL, text_color=T.TEXT, anchor="w").pack(
                side="left", padx=T.S3, pady=T.S2)
            C.badge(srow, "Available" if slot["is_available"] else "Blocked",
                    color=T.SUCCESS if slot["is_available"] else T.TEXT_MUTED).pack(
                side="right", padx=T.S3)
    else:
        ctk.CTkLabel(right, text="No availability slots recorded.", font=T.F_SMALL,
                     text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=(T.S5, 0))
    C.mk_button(footer, "Close", dlg.destroy, kind="secondary", width=130,
                height=42).pack(side="right")

    def edit():
        dlg.destroy()
        open_artist_dialog(app, artist_id=artist_id)

    C.primary_button(footer, "Edit artist", edit, width=180,
                     height=42).pack(side="right", padx=(0, T.S3))


# ---------------------------------------------------------------------------
# Availability manager
# ---------------------------------------------------------------------------
def build_availability_manager(app):
    _begin(app, "availability")
    _set_title(app, "Availability", "Manage artist working hours and bookable slots")
    wrap = _page(app)

    actions = C.page_header(wrap, "Artist availability",
                            "Add bookable windows for each artist")
    C.mk_button(actions, "Refresh", lambda: build_availability_manager(app),
                kind="secondary", icon=C.G_REFRESH, width=120, height=42).pack(side="right")

    artists = list(get_all_artists_admin() or [])
    id_map = {a["full_name"]: a["artist_id"] for a in artists}
    names = list(id_map.keys())

    form_card = C.card(wrap)
    form_card.pack(fill="x", pady=(0, T.S4))
    inner = ctk.CTkFrame(form_card, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)

    ctk.CTkLabel(inner, text="Artist", font=T.F_LABEL, text_color=T.TEXT_SEC,
                 anchor="w").pack(anchor="w")
    artist_var = ctk.StringVar(value=names[0] if names else "")
    C.combo(inner, names or ["No artists"], variable=artist_var, width=260).pack(
        anchor="w", pady=(0, T.S3))

    fields = ctk.CTkFrame(inner, fg_color="transparent")
    fields.pack(fill="x")
    f_date, e_date = C.labeled_entry(fields, "Date (YYYY-MM-DD)", datetime.now().date().isoformat())
    f_date.pack(side="left", fill="x", expand=True, padx=(0, T.S3))
    f_start, e_start = C.labeled_entry(fields, "Start (HH:MM)", "09:00", height=40)
    f_start.pack(side="left", padx=(0, T.S3))
    f_end, e_end = C.labeled_entry(fields, "End (HH:MM)", "13:00", height=40)
    f_end.pack(side="left")
    e_start.configure(width=120)
    e_end.configure(width=120)

    table = C.DataTable(wrap, [
        ("id", "ID", 60, "center"),
        ("artist", "Artist", 220, "w"),
        ("date", "Date", 140, "w"),
        ("start", "Start", 110, "center"),
        ("end", "End", 110, "center"),
        ("available", "Available", 120, "center"),
    ], height=13)
    table.pack(fill="both", expand=True, pady=(0, T.S4))

    def load():
        rows = []
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT av.availability_id, ar.full_name, av.available_date, "
                "av.start_time, av.end_time, av.is_available "
                "FROM artist_availability av LEFT JOIN artists ar "
                "ON av.artist_id = ar.artist_id ORDER BY av.available_date DESC LIMIT 200")
            for row in cur.fetchall():
                rows.append(((
                    row["availability_id"], row["full_name"] or "—", row["available_date"],
                    row["start_time"], row["end_time"],
                    "Yes" if row["is_available"] else "No",
                ), None))
        finally:
            conn.close()
        table.set_rows(rows)

    def add_slot():
        aid = id_map.get(artist_var.get())
        if not aid:
            C.toast(app, "Select an artist first.", "warning")
            return
        date_str = e_date.get().strip()
        start = e_start.get().strip()
        end = e_end.get().strip()
        if not date_str or not start or not end:
            C.toast(app, "Fill in date, start and end time.", "warning")
            return
        try:
            if time_to_minutes(start) >= time_to_minutes(end):
                C.toast(app, "Start time must be before end time.", "warning")
                return
        except Exception:
            C.toast(app, "Invalid time format (HH:MM).", "warning")
            return
        add_availability(aid, date_str, start, end)
        load()
        C.toast(app, "Availability added for {}.".format(artist_var.get()), "success")

    C.primary_button(inner, "Add availability", add_slot, icon=C.G_PLUS, width=200,
                     height=42).pack(anchor="w", pady=(T.S4, 0))
    load()

    def toggle_selected():
        vals = table.selected_values()
        if not vals:
            C.toast(app, "Select a row first.", "warning")
            return
        new_val = 0 if vals[5] == "Yes" else 1
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE artist_availability SET is_available = ? "
                        "WHERE availability_id = ?", (new_val, int(vals[0])))
            conn.commit()
        finally:
            conn.close()
        load()
        C.toast(app, "Slot marked {}.".format("available" if new_val else "unavailable"),
                "success")

    btns = ctk.CTkFrame(wrap, fg_color="transparent")
    btns.pack(fill="x")
    C.mk_button(btns, "Toggle available", toggle_selected, kind="secondary",
                icon=C.G_CHECK, width=180, height=42).pack(side="left")


# ---------------------------------------------------------------------------
# Add-on manager
# ---------------------------------------------------------------------------
def build_addon_manager(app):
    _begin(app, "addons")
    _set_title(app, "Add-ons", "Optional extras offered with bookings")
    wrap = _page(app)

    actions = C.page_header(wrap, "Add-on management",
                            "Extras such as touch-ups, aftercare and extended sessions")
    C.primary_button(actions, "Add add-on", lambda: open_addon_dialog(app),
                     icon=C.G_PLUS, width=150, height=42).pack(side="right")
    C.mk_button(actions, "Refresh", lambda: build_addon_manager(app),
                kind="secondary", icon=C.G_REFRESH, width=120, height=42).pack(
        side="right", padx=(0, T.S3))

    bar = C.card(wrap)
    bar.pack(fill="x", pady=(0, T.S4))
    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)
    search_wrap, ent = C.search_entry(inner, "Search add-ons…", width=300)
    search_wrap.pack(side="left")
    count_lbl = ctk.CTkLabel(inner, text="", font=T.F_SMALL, text_color=T.TEXT_MUTED)
    count_lbl.pack(side="right")

    table = C.DataTable(wrap, [
        ("id", "ID", 60, "center"),
        ("name", "Add-on", 320, "w"),
        ("description", "Description", 360, "w"),
        ("price", "Price", 110, "e"),
        ("active", "Active", 90, "center"),
    ], height=15)
    table.pack(fill="both", expand=True)

    state = {"term": ""}

    def load():
        rows = []
        term = state["term"].lower()
        for a in get_all_addons_admin():
            vals = (a["addon_id"], a["addon_name"], a["description"] or "—",
                    _money(a["price"]), "Yes" if a["is_active"] else "No")
            if not _search_filter(vals, term):
                continue
            rows.append((vals, None))
        table.set_rows(rows)
        count_lbl.configure(text="{} add-on{}".format(len(rows),
                                                      "" if len(rows) == 1 else "s"))

    def on_search(_=None):
        state["term"] = ent.get().strip()
        load()

    ent.bind("<KeyRelease>", on_search)
    load()

    def edit_selected():
        vals = table.selected_values()
        if not vals:
            C.toast(app, "Select an add-on first.", "warning")
            return
        open_addon_dialog(app, addon_id=int(vals[0]))

    def deactivate_selected():
        vals = table.selected_values()
        if not vals:
            C.toast(app, "Select an add-on first.", "warning")
            return
        addon_id, name = int(vals[0]), vals[1]

        def do_it():
            deactivate_addon(addon_id)
            load()
            C.toast(app, "Add-on deactivated.", "success")

        C.confirm_dialog(app, "Deactivate add-on",
                         "Deactivate '{}'?".format(name), do_it,
                         confirm_text="Deactivate", kind="danger")

    btns = ctk.CTkFrame(wrap, fg_color="transparent")
    btns.pack(fill="x", pady=(T.S4, 0))
    C.mk_button(btns, "Edit selected", edit_selected, kind="secondary", icon=C.G_PEN,
                width=170, height=42).pack(side="left")
    C.mk_button(btns, "Deactivate", deactivate_selected, kind="danger", icon=C.G_TRASH,
                width=150, height=42).pack(side="left", padx=(T.S3, 0))


def open_addon_dialog(app, addon_id=None):
    is_edit = addon_id is not None
    addon = None
    if is_edit:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM package_addons WHERE addon_id = ?", (addon_id,))
            addon = cur.fetchone()
        finally:
            conn.close()

    dlg, body = _dialog(app, "Edit add-on" if is_edit else "Add add-on",
                        560, 480, icon=C.G_PLUS)

    f_name, e_name = C.labeled_entry(body, "Add-on name *", "e.g. Numbing Cream")
    f_name.pack(fill="x", pady=(0, T.S3))
    f_price, e_price = C.labeled_entry(body, "Price *", "0.00")
    f_price.pack(fill="x", pady=(0, T.S3))

    C.field_label(body, "Description").pack(anchor="w")
    txt_desc = C.text_area(body, height=120)
    txt_desc.pack(fill="x")

    if is_edit and addon:
        e_name.insert(0, addon["addon_name"] or "")
        e_price.insert(0, "{:.2f}".format(float(addon["price"])))
        txt_desc.insert("1.0", addon["description"] or "")

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=(T.S5, 0))

    def save():
        name = e_name.get().strip()
        try:
            price = float(e_price.get())
        except ValueError:
            C.alert_dialog(app, "Invalid input", "Price must be a number.", "error")
            return
        if not name or price < 0:
            C.alert_dialog(app, "Invalid input", "Name and a valid price are required.",
                           "error")
            return
        description = txt_desc.get("1.0", "end-1c").strip()
        if is_edit:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("UPDATE package_addons SET addon_name=?, description=?, price=? "
                            "WHERE addon_id=?", (name, description, price, addon_id))
                conn.commit()
            finally:
                conn.close()
        else:
            add_addon(name, description, price)
        dlg.destroy()
        C.toast(app, "Add-on {}.".format("updated" if is_edit else "created"), "success")
        build_addon_manager(app)

    C.mk_button(footer, "Cancel", dlg.destroy, kind="secondary", width=130,
                height=42).pack(side="right")
    C.primary_button(footer, "Save add-on", save, width=180,
                     height=42).pack(side="right", padx=(0, T.S3))


# ---------------------------------------------------------------------------
# Booking manager
# ---------------------------------------------------------------------------
def build_booking_manager(app):
    _begin(app, "bookings")
    _set_title(app, "Bookings", "Review, confirm and manage every appointment")
    wrap = _page(app)

    actions = C.page_header(wrap, "Booking management",
                            "Approve requests and keep the schedule accurate")
    C.mk_button(actions, "Refresh", lambda: build_booking_manager(app),
                kind="secondary", icon=C.G_REFRESH, width=120, height=42).pack(side="right")

    bar = C.card(wrap)
    bar.pack(fill="x", pady=(0, T.S4))
    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)
    search_wrap, ent = C.search_entry(inner, "Search bookings…", width=280)
    search_wrap.pack(side="left")
    status_var = ctk.StringVar(value="All statuses")
    C.combo(inner, ["All statuses"] + BOOKING_STATUSES, variable=status_var,
            width=180).pack(side="left", padx=T.S3)
    count_lbl = ctk.CTkLabel(inner, text="", font=T.F_SMALL, text_color=T.TEXT_MUTED)
    count_lbl.pack(side="right")

    table = C.DataTable(wrap, [
        ("id", "ID", 55, "center"),
        ("reference", "Reference", 170, "w"),
        ("customer", "Customer", 180, "w"),
        ("package", "Design", 190, "w"),
        ("artist", "Artist", 160, "w"),
        ("date", "Date", 110, "w"),
        ("time", "Time", 140, "center"),
        ("status", "Status", 110, "center"),
        ("payment", "Payment", 110, "center"),
    ], height=15)
    table.pack(fill="both", expand=True)

    state = {"term": ""}

    def load():
        rows = []
        term = state["term"].lower()
        chosen_status = status_var.get()
        for b in get_all_bookings_admin():
            vals = (b["booking_id"], b["booking_reference"], b["customer_name"] or "—",
                    b["package_name"] or "—", b["artist_name"] or "—",
                    b["appointment_date"],
                    "{} - {}".format(b["start_time"], b["end_time"]),
                    b["booking_status"], b["payment_status"] or "Pending")
            if chosen_status != "All statuses" and b["booking_status"] != chosen_status:
                continue
            if not _search_filter(vals, term):
                continue
            rows.append((vals, None))
        table.set_rows(rows)
        count_lbl.configure(text="{} booking{}".format(len(rows),
                                                       "" if len(rows) == 1 else "s"))

    def on_search(_=None):
        state["term"] = ent.get().strip()
        load()

    ent.bind("<KeyRelease>", on_search)
    status_var.trace_add("write", lambda *_: load())
    load()

    def selected_booking():
        vals = table.selected_values()
        if not vals:
            C.toast(app, "Select a booking first.", "warning")
            return None
        return int(vals[0]), vals[1], vals[7]

    def change_status(new_status):
        res = selected_booking()
        if not res:
            return
        booking_id, reference, current = res
        if current == new_status:
            C.toast(app, "Booking is already {}.".format(new_status.lower()), "info")
            return
        danger = new_status in ("Rejected", "Cancelled")

        def do_it():
            ok, msg = update_booking_status(booking_id, new_status,
                                            app.current_admin["admin_id"],
                                            "Changed by admin")
            if ok:
                C.toast(app, "Booking {} marked {}.".format(reference, new_status.lower()),
                        "success")
                load()
            else:
                C.alert_dialog(app, "Status update failed", msg, "error")

        C.confirm_dialog(app, "Mark as {}".format(new_status),
                         "Change booking {} from '{}' to '{}'?".format(reference, current,
                                                                      new_status),
                         do_it, confirm_text="Mark {}".format(new_status),
                         kind="danger" if danger else "primary")

    def open_history():
        res = selected_booking()
        if res:
            view_history(app, res[0], res[1])

    def open_details():
        res = selected_booking()
        if res:
            open_booking_details(app, res[0])

    table.tree.bind("<Double-1>", lambda e: open_details())

    btns = ctk.CTkFrame(wrap, fg_color="transparent")
    btns.pack(fill="x", pady=(T.S4, 0))
    C.primary_button(btns, "Confirm", lambda: change_status("Confirmed"), icon=C.G_CHECK,
                     width=130, height=42).pack(side="left")
    C.mk_button(btns, "Complete", lambda: change_status("Completed"), kind="success",
                icon=C.G_STAR, width=140, height=42).pack(side="left", padx=(T.S2, 0))
    C.mk_button(btns, "Reject", lambda: change_status("Rejected"), kind="danger",
                icon=C.G_CLOSE, width=120, height=42).pack(side="left", padx=(T.S2, 0))
    C.mk_button(btns, "Cancel", lambda: change_status("Cancelled"), kind="danger",
                icon=C.G_CLOSE, width=120, height=42).pack(side="left", padx=(T.S2, 0))
    C.mk_button(btns, "View history", open_history, kind="secondary", icon=C.G_CLOCK,
                width=160, height=42).pack(side="right")
    C.primary_button(btns, "View details", open_details, icon=C.G_SEARCH,
                     width=160, height=42).pack(side="right", padx=(0, T.S3))


def view_history(app, booking_id, reference):
    dlg, body = _dialog(app, "Status history", 760, 520, icon=C.G_CLOCK)
    ctk.CTkLabel(body, text="Booking {}".format(reference), font=T.F_SMALL,
                 text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(0, T.S3))

    table = C.DataTable(body, [
        ("prev", "Previous", 140, "w"),
        ("new", "New status", 140, "w"),
        ("admin", "Changed by", 180, "w"),
        ("notes", "Notes", 240, "w"),
        ("changed_at", "Changed at", 190, "w"),
    ], height=9)
    table.pack(fill="both", expand=True)

    history = list(get_status_history(booking_id) or [])
    if history:
        table.set_rows([((
            h["previous_status"] or "—", h["new_status"], h["admin_name"] or "Customer",
            h["notes"] or "—", str(h["changed_at"]).replace("T", " ")[:16],
        ), None) for h in history])
    else:
        table.set_rows([])

    C.mk_button(body, "Close", dlg.destroy, kind="secondary", width=130,
                height=42).pack(anchor="e", pady=(T.S4, 0))


def open_booking_details(app, booking_id):
    """In-depth, database-backed booking view with inline status/payment updates."""
    b = get_booking_full(booking_id)
    if not b:
        C.toast(app, "Booking not found.", "error")
        return

    reference = b["booking_reference"]
    payments = list(get_payments_for_booking(booking_id) or [])
    addons = list(get_booking_addons(booking_id) or [])
    total = float(b["total_price"] or 0)
    settled = sum(float(p["amount"] or 0) for p in payments if p["payment_status"] == "Paid")
    balance = max(total - settled, 0.0)

    dlg, body = _dialog(app, "Booking details", 960, 680, icon=C.G_CAL)

    def reopen():
        open_booking_details(app, booking_id)

    def apply_status(new_status):
        if new_status == b["booking_status"]:
            C.toast(app, "Booking is already {}.".format(new_status.lower()), "info")
            return

        def do_it():
            ok, msg = update_booking_status(booking_id, new_status,
                                            app.current_admin["admin_id"],
                                            "Updated from booking details")
            if ok:
                C.toast(app, "Booking {} marked {}.".format(reference, new_status.lower()),
                        "success")
                dlg.destroy()
                reopen()
            else:
                C.alert_dialog(app, "Status update failed", msg, "error")

        C.confirm_dialog(app, "Mark as {}".format(new_status),
                         "Change booking {} from '{}' to '{}'?".format(
                             reference, b["booking_status"], new_status),
                         do_it, confirm_text="Mark {}".format(new_status),
                         kind="danger" if new_status in ("Rejected", "Cancelled") else "primary")

    def record_payment_here():
        open_payment_dialog(app, booking_ref=reference,
                            on_saved=lambda: (dlg.destroy(), reopen()))

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True)

    # -- left: reference image + payment summary -----------------------------
    left = ctk.CTkFrame(cols, fg_color="transparent", width=300)
    left.pack(side="left", fill="y", padx=(0, T.S5))
    left.pack_propagate(False)
    C.image_label(left, b["reference_image_path"], (300, 200), radius=T.RADIUS_LG,
                  fallback="No reference image").pack()
    ctk.CTkLabel(left, text="Reference image", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(T.S3, 0))

    fin = ctk.CTkFrame(left, fg_color=T.ELEVATED, corner_radius=T.RADIUS)
    fin.pack(fill="x", pady=(T.S4, 0))
    ctk.CTkLabel(fin, text="PAYMENT SUMMARY", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", padx=T.S3, pady=(T.S3, T.S2))
    for label, value, color in [
        ("Total", _money(total), T.TEXT),
        ("Paid to date", _money(settled), T.SUCCESS),
        ("Balance", _money(balance), T.RED if balance > 0 else T.TEXT),
    ]:
        prow = ctk.CTkFrame(fin, fg_color="transparent")
        prow.pack(fill="x", padx=T.S3, pady=(0, T.S2))
        ctk.CTkLabel(prow, text=label, font=T.F_SMALL, text_color=T.TEXT_SEC,
                     anchor="w").pack(side="left")
        ctk.CTkLabel(prow, text=value, font=T.F_BODY, text_color=color,
                     anchor="e").pack(side="right")
    C.badge(fin, b["payment_status"],
            color=PAYMENT_STATUS_COLORS.get(b["payment_status"], T.TEXT_MUTED)).pack(
        anchor="w", padx=T.S3, pady=(0, T.S3))

    # -- right: everything else ---------------------------------------------
    right = C.scroll_area(cols)
    right.pack(side="right", fill="both", expand=True)

    ctk.CTkLabel(right, text="Booking {}".format(reference), font=T.F_H2,
                 text_color=T.TEXT, anchor="w").pack(anchor="w")

    tags = ctk.CTkFrame(right, fg_color="transparent")
    tags.pack(anchor="w", pady=(T.S3, T.S4))
    C.badge(tags, b["booking_status"],
            color=BOOKING_STATUS_COLORS.get(b["booking_status"], T.TEXT_MUTED)).pack(side="left")
    C.badge(tags, "Payment: {}".format(b["payment_status"]),
            color=PAYMENT_STATUS_COLORS.get(b["payment_status"], T.TEXT_MUTED)).pack(
        side="left", padx=(T.S2, 0))

    contact = "   ·   ".join([x for x in (b["customer_email"], b["customer_phone"]) if x])
    facts = ctk.CTkFrame(right, fg_color="transparent")
    facts.pack(fill="x")
    for label, value in [
        ("Customer", b["customer_name"]),
        ("Contact", contact or "—"),
        ("Design", b["package_name"] or "—"),
        ("Type", "Individual tattoo" if b["package_kind"] == "Tattoo" else "Package"),
        ("Category", b["package_category"] or "—"),
        ("Artist", b["artist_name"] or "—"),
        ("Appointment", "{}   ·   {} – {}".format(
            b["appointment_date"], b["start_time"], b["end_time"])),
        ("Placement", b["placement"]),
        ("Size", b["tattoo_size"]),
        ("Base price", _money(b["base_price"])),
        ("Add-ons", _money(b["additional_cost"])),
        ("Total price", _money(b["total_price"])),
    ]:
        _detail_row(facts, label, value)

    C.divider(right, pady=(T.S2, T.S3))
    _detail_row(right, "Design description", b["design_description"] or "—")
    _detail_row(right, "Customer notes", b["customer_notes"] or "—")

    ctk.CTkLabel(right, text="ADD-ONS", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(T.S2, T.S2))
    if addons:
        for a in addons:
            arow = ctk.CTkFrame(right, fg_color=T.ELEVATED, corner_radius=T.RADIUS)
            arow.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(arow, text="{}   ×{}".format(a["addon_name"] or "Add-on", a["quantity"]),
                         font=T.F_SMALL, text_color=T.TEXT, anchor="w").pack(
                side="left", padx=T.S3, pady=T.S2)
            ctk.CTkLabel(arow, text=_money(float(a["unit_price"] or 0) * int(a["quantity"] or 0)),
                         font=T.F_SMALL, text_color=T.TEXT_SEC, anchor="e").pack(
                side="right", padx=T.S3)
    else:
        ctk.CTkLabel(right, text="No add-ons on this booking.", font=T.F_SMALL,
                     text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")

    C.divider(right, pady=(T.S3, T.S3))
    ctk.CTkLabel(right, text="PAYMENTS", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(0, T.S2))
    if payments:
        ptable = C.DataTable(right, [
            ("amount", "Amount", 110, "e"),
            ("method", "Method", 120, "w"),
            ("ref", "Reference", 150, "w"),
            ("status", "Status", 100, "center"),
            ("paid_at", "Paid at", 150, "w"),
        ], height=4, sortable=False)
        ptable.pack(fill="x")
        ptable.set_rows([((
            _money(p["amount"]), p["payment_method"] or "—", p["payment_reference"] or "—",
            p["payment_status"],
            str(p["paid_at"]).replace("T", " ")[:16] if p["paid_at"] else "—",
        ), None) for p in payments])
    else:
        ctk.CTkLabel(right, text="No payments recorded yet — use \"Record payment\" below.",
                     font=T.F_SMALL, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")

    C.divider(right, pady=(T.S3, T.S3))
    ctk.CTkLabel(right, text="UPDATE STATUS", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(0, T.S2))
    allowed = list(VALID_TRANSITIONS.get(b["booking_status"], []))
    if allowed:
        srow = ctk.CTkFrame(right, fg_color="transparent")
        srow.pack(fill="x")
        status_var = ctk.StringVar(value=allowed[0])
        C.combo(srow, allowed, variable=status_var, width=200).pack(side="left")
        C.primary_button(srow, "Apply", lambda: apply_status(status_var.get()),
                         width=120, height=40).pack(side="left", padx=(T.S3, 0))
        ctk.CTkLabel(right, text="Completing a booking requires it to be fully paid.",
                     font=T.F_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(
            anchor="w", pady=(T.S2, 0))
    else:
        ctk.CTkLabel(right, text="This booking is closed — no further status changes.",
                     font=T.F_SMALL, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")

    C.divider(right, pady=(T.S3, T.S3))
    ctk.CTkLabel(right, text="ADMIN NOTES", font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w", pady=(0, T.S2))
    notes_box = ctk.CTkTextbox(right, height=80, font=T.F_SMALL)
    notes_box.pack(fill="x")
    if b["admin_notes"]:
        notes_box.insert("1.0", b["admin_notes"])

    def save_notes():
        update_booking_notes(booking_id, notes_box.get("1.0", "end").strip())
        C.toast(app, "Notes saved.", "success")

    C.mk_button(right, "Save note", save_notes, kind="secondary", icon=C.G_PEN,
                width=140, height=38).pack(anchor="w", pady=(T.S2, T.S6))

    # -- footer --------------------------------------------------------------
    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=(T.S5, 0))
    C.mk_button(footer, "Close", dlg.destroy, kind="secondary", width=120,
                height=42).pack(side="right")
    C.mk_button(footer, "View history", lambda: view_history(app, booking_id, reference),
                kind="secondary", icon=C.G_CLOCK, width=160, height=42).pack(
        side="right", padx=(0, T.S3))
    C.primary_button(footer, "Record payment", record_payment_here, icon=C.G_CASH,
                     width=190, height=42).pack(side="right", padx=(0, T.S3))


# ---------------------------------------------------------------------------
# Payment manager
# ---------------------------------------------------------------------------
def build_payment_manager(app):
    _begin(app, "payments")
    _set_title(app, "Payments", "Record and review customer payments")
    wrap = _page(app)

    actions = C.page_header(wrap, "Payment management",
                            "Deposits, final payments and refunds")
    C.primary_button(actions, "Record payment", lambda: open_payment_dialog(app),
                     icon=C.G_CASH, width=180, height=42).pack(side="right")
    C.mk_button(actions, "Refresh", lambda: build_payment_manager(app),
                kind="secondary", icon=C.G_REFRESH, width=120, height=42).pack(
        side="right", padx=(0, T.S3))

    bar = C.card(wrap)
    bar.pack(fill="x", pady=(0, T.S4))
    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)
    search_wrap, ent = C.search_entry(inner, "Search payments…", width=280)
    search_wrap.pack(side="left")
    status_var = ctk.StringVar(value="All statuses")
    C.combo(inner, ["All statuses"] + PAYMENT_STATUSES, variable=status_var,
            width=180).pack(side="left", padx=T.S3)
    count_lbl = ctk.CTkLabel(inner, text="", font=T.F_SMALL, text_color=T.TEXT_MUTED)
    count_lbl.pack(side="right")

    table = C.DataTable(wrap, [
        ("id", "ID", 55, "center"),
        ("reference", "Booking", 170, "w"),
        ("customer", "Customer", 200, "w"),
        ("amount", "Amount", 110, "e"),
        ("method", "Method", 140, "w"),
        ("ref", "Reference", 170, "w"),
        ("status", "Status", 110, "center"),
        ("paid_at", "Paid at", 170, "w"),
    ], height=15)
    table.pack(fill="both", expand=True)

    state = {"term": ""}

    def load():
        rows = []
        term = state["term"].lower()
        chosen_status = status_var.get()
        for p in get_payments():
            vals = (p["payment_id"], p["booking_reference"] or "—",
                    p["customer_name"] or "—", _money(p["amount"]),
                    p["payment_method"] or "—", p["payment_reference"] or "—",
                    p["payment_status"],
                    str(p["paid_at"]).replace("T", " ")[:16] if p["paid_at"] else "—")
            if chosen_status != "All statuses" and p["payment_status"] != chosen_status:
                continue
            if not _search_filter(vals, term):
                continue
            rows.append((vals, None))
        table.set_rows(rows)
        count_lbl.configure(text="{} payment{}".format(len(rows),
                                                       "" if len(rows) == 1 else "s"))

    def on_search(_=None):
        state["term"] = ent.get().strip()
        load()

    ent.bind("<KeyRelease>", on_search)
    status_var.trace_add("write", lambda *_: load())
    load()

    def record_for_selected():
        vals = table.selected_values()
        if not vals:
            C.toast(app, "Select a payment row first.", "warning")
            return
        open_payment_dialog(app, booking_ref=vals[1],
                            amount_str=str(vals[3]).replace("₱", "").strip())

    btns = ctk.CTkFrame(wrap, fg_color="transparent")
    btns.pack(fill="x", pady=(T.S4, 0))
    C.mk_button(btns, "Record for selected booking", record_for_selected, kind="secondary",
                icon=C.G_CASH, width=260, height=42).pack(side="left")


def open_payment_dialog(app, booking_ref=None, amount_str="", on_saved=None):
    dlg, body = _dialog(app, "Record payment", 560, 520, icon=C.G_CASH)

    f_ref, e_ref = C.labeled_entry(body, "Booking reference *", "TAT-…")
    f_ref.pack(fill="x", pady=(0, T.S3))
    f_amount, e_amount = C.labeled_entry(body, "Amount *", "0.00")
    f_amount.pack(fill="x", pady=(0, T.S3))

    prow = ctk.CTkFrame(body, fg_color="transparent")
    prow.pack(fill="x", pady=(0, T.S3))
    f_method, e_method = C.labeled_entry(prow, "Method", "Cash / Card", height=40)
    f_method.pack(side="left", fill="x", expand=True, padx=(0, T.S3))
    f_refno, e_refno = C.labeled_entry(prow, "Payment reference", "Optional", height=40)
    f_refno.pack(side="left", fill="x", expand=True)

    C.field_label(body, "Payment status").pack(anchor="w")
    status_var = ctk.StringVar(value="Paid")
    C.combo(body, PAYMENT_STATUSES, variable=status_var, width=200).pack(anchor="w")

    if booking_ref:
        e_ref.insert(0, booking_ref)
    if amount_str:
        e_amount.insert(0, amount_str)

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=(T.S5, 0))

    def save():
        reference = e_ref.get().strip()
        try:
            amount = float(e_amount.get())
        except ValueError:
            C.alert_dialog(app, "Invalid input", "Amount must be a number.", "error")
            return
        if not reference or amount < 0:
            C.alert_dialog(app, "Invalid input",
                           "A booking reference and a valid amount are required.", "error")
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT booking_id FROM bookings WHERE booking_reference = ?",
                        (reference,))
            row = cur.fetchone()
        finally:
            conn.close()
        if not row:
            C.alert_dialog(app, "Not found",
                           "No booking matches reference '{}'.".format(reference), "error")
            return
        record_payment(row["booking_id"], amount, e_method.get().strip() or None,
                       e_refno.get().strip() or None, status_var.get())
        dlg.destroy()
        C.toast(app, "Payment recorded.", "success")
        if on_saved:
            on_saved()
        else:
            build_payment_manager(app)

    C.mk_button(footer, "Cancel", dlg.destroy, kind="secondary", width=130,
                height=42).pack(side="right")
    C.primary_button(footer, "Save payment", save, width=180,
                     height=42).pack(side="right", padx=(0, T.S3))


# ---------------------------------------------------------------------------
# Customer manager
# ---------------------------------------------------------------------------
def build_customer_manager(app):
    _begin(app, "customers")
    _set_title(app, "Customers", "Registered studio clients")
    wrap = _page(app)

    actions = C.page_header(wrap, "Customer directory",
                            "Active accounts registered with the studio")
    C.mk_button(actions, "Refresh", lambda: build_customer_manager(app),
                kind="secondary", icon=C.G_REFRESH, width=120, height=42).pack(side="right")

    bar = C.card(wrap)
    bar.pack(fill="x", pady=(0, T.S4))
    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)
    search_wrap, ent = C.search_entry(inner, "Search customers…", width=300)
    search_wrap.pack(side="left")
    count_lbl = ctk.CTkLabel(inner, text="", font=T.F_SMALL, text_color=T.TEXT_MUTED)
    count_lbl.pack(side="right")

    table = C.DataTable(wrap, [
        ("id", "ID", 60, "center"),
        ("name", "Name", 240, "w"),
        ("email", "Email", 260, "w"),
        ("phone", "Phone", 170, "w"),
        ("active", "Active", 90, "center"),
    ], height=16)
    table.pack(fill="both", expand=True)

    state = {"term": ""}

    def load():
        rows = []
        term = state["term"].lower()
        for u in get_customers():
            name = " ".join(p for p in [u["first_name"], u["middle_name"], u["last_name"]] if p)
            vals = (u["user_id"], name, u["email"] or "—", u["phone"] or "—",
                    "Yes" if u["is_active"] else "No")
            if not _search_filter(vals, term):
                continue
            rows.append((vals, None))
        table.set_rows(rows)
        count_lbl.configure(text="{} customer{}".format(len(rows),
                                                        "" if len(rows) == 1 else "s"))

    def on_search(_=None):
        state["term"] = ent.get().strip()
        load()

    ent.bind("<KeyRelease>", on_search)
    load()
