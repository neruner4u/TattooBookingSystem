"""Customer-facing screens — premium dark tattoo-studio experience.

Every screen renders inside ``app.content_frame`` (the shell in main.py) and
reuses the shared widgets from ``components`` so the whole app stays visually
consistent.
"""
from datetime import datetime, timedelta
import os
import shutil
import uuid
from tkinter import filedialog

import customtkinter as ctk

import theme as T
import components as C
import booking as booking_mod
from database import (
    REF_IMG_DIR,
    get_active_packages, get_package, get_categories, search_packages,
    get_active_artists, get_availability, get_addons,
    get_bookings_by_user, get_booking_by_reference, get_connection,
)

STEPS = ["Artist", "Date", "Time", "Details", "Add-ons"]


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------
def money(value):
    return "₱ {:.2f}".format(float(value or 0))


def initials(name):
    parts = [p for p in str(name or "").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def _begin(app, nav_key=None):
    app.clear_content()
    if nav_key is not None:
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


def _scroll(app):
    area = C.scroll_area(app.content_frame)
    area.pack(fill="both", expand=True)
    return area


def _image_label(parent, path, size, radius=T.RADIUS, fallback="No image"):
    return C.image_label(parent, path, size, radius=radius, fallback=fallback)


def _responsive_grid(parent, cols, uniform="col"):
    grid = ctk.CTkFrame(parent, fg_color="transparent")
    grid.pack(fill="x")
    for i in range(cols):
        grid.grid_columnconfigure(i, weight=1, uniform=uniform)
    return grid


# ---------------------------------------------------------------------------
# Package card
# ---------------------------------------------------------------------------
def package_card(parent, pkg, on_book, on_view=None, img_size=(280, 160)):
    card = C.hover_card(parent)

    cover = C.CoverImage(card, pkg["image_path"], height=img_size[1],
                         radius=T.RADIUS_LG, bg=T.CARD)
    cover.pack(fill="x")

    body = ctk.CTkFrame(card, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=T.S4, pady=T.S4)

    top = ctk.CTkFrame(body, fg_color="transparent")
    top.pack(fill="x")
    ctk.CTkLabel(top, text=pkg["category"].upper(), font=T.F_LABEL,
                 text_color=T.RED).pack(side="left")
    ctk.CTkLabel(top, text="{} min".format(pkg["duration_minutes"]), font=T.F_TINY,
                 text_color=T.TEXT_MUTED).pack(side="right")

    name = ctk.CTkLabel(body, text=pkg["package_name"], font=T.F_H3, text_color=T.TEXT,
                        anchor="w", justify="left")
    name.pack(anchor="w", pady=(6, 2), fill="x")

    desc = (pkg["description"] or "").strip()
    if desc:
        ctk.CTkLabel(body, text=desc, font=T.F_TINY, text_color=T.TEXT_MUTED,
                     anchor="w", justify="left", wraplength=img_size[0] - 40,
                     height=30).pack(anchor="w", fill="x")

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(side="bottom", fill="x", pady=(T.S3, 0))
    ctk.CTkLabel(footer, text=money(pkg["price"]), font=(T.FAMILY, 16, "bold"),
                 text_color=T.TEXT).pack(side="left")
    C.primary_button(footer, "Book", lambda p=pkg: on_book(p["package_id"]),
                     width=84, height=34).pack(side="right")

    if on_view is not None:
        for widget in C._walk(card):
            if widget is not card and isinstance(
                    widget, (ctk.CTkFrame, ctk.CTkLabel, C.CoverImage)):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda e, p=pkg: on_view(p["package_id"]))
        for widget in C._walk(card):
            if isinstance(widget, ctk.CTkButton):
                widget.unbind("<Button-1>")
    return card


# ---------------------------------------------------------------------------
# HOME
# ---------------------------------------------------------------------------
def build_home(app):
    if getattr(app, "pending_package_id", None):
        pkg_id = app.pending_package_id
        app.pending_package_id = None
        start_booking_flow(app, pkg_id)
        return

    _begin(app, "home")
    _set_title(app, "Home", "Your tattoo journey at a glance")
    scroll = _scroll(app)

    user = app.current_user or {}
    first_name = user.get("first_name") or "there"

    _hero(scroll, app)

    ctk.CTkLabel(scroll, text="Welcome back, {}.".format(first_name), font=T.F_H1,
                 text_color=T.TEXT, anchor="w").pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(scroll, text="Here is everything happening in your studio account.",
                 font=T.F_SMALL, text_color=T.TEXT_MUTED, anchor="w").pack(
        anchor="w", pady=(0, T.S5))

    _quick_actions(scroll, app)

    bookings = list(get_bookings_by_user(user.get("user_id", -1)) or [])
    _upcoming_appointment(scroll, app, bookings)

    _featured_artists(scroll, app)
    _featured_packages(scroll, app)
    _featured_packages(scroll, app, kind="Tattoo")
    _recent_bookings(scroll, app, bookings)


def _hero(scroll, app):
    hero = ctk.CTkFrame(scroll, fg_color=T.SURFACE, corner_radius=T.RADIUS_LG,
                        height=300)
    hero.pack(fill="x", pady=(0, T.S6))
    hero.pack_propagate(False)

    def paint(canvas, w, h):
        pad = T.S6
        canvas.create_text(pad, h * 0.25, anchor="w",
                           text="EST. 2014   ·   PRIVATE STUDIOS   ·   AWARD WINNING",
                           fill=T.RED, font=(T.FAMILY, 10, "bold"))
        canvas.create_text(pad, h * 0.44, anchor="w", text="Your story,",
                           fill=T.TEXT, font=(T.FAMILY, 32, "bold"))
        canvas.create_text(pad, h * 0.44 + 42, anchor="w", text="inked forever.",
                           fill=T.TEXT, font=(T.FAMILY, 32, "bold"))
        canvas.create_text(pad, h * 0.78, anchor="w",
                           text="Book award-winning artists, browse signature styles and "
                                "manage every appointment in one place.",
                           fill=T.TEXT_SEC, font=(T.FAMILY, 12),
                           width=max(w - pad * 2, 260))

    C.CoverImage(hero, radius=T.RADIUS_LG, bg=T.SURFACE, overlay=paint,
                 gradient=(T.HERO_GRAD_FROM, T.HERO_GRAD_TO, "horizontal")).place(
        x=0, y=0, relwidth=1, relheight=1)


def _quick_actions(scroll, app):
    row = ctk.CTkFrame(scroll, fg_color="transparent")
    row.pack(fill="x", pady=(0, T.S6))

    actions = [
        (C.G_GRID, "Book a package", "Bundle a full session in minutes",
         lambda: build_package_list(app), T.RED),
        (C.G_PEN, "Book a tattoo", "Grab a single piece — no package needed",
         lambda: build_package_list(app, kind="Tattoo"), T.GOLD),
        (C.G_GALLERY, "Explore the gallery", "Browse signature tattoo styles",
         lambda: build_gallery(app), T.INFO),
        (C.G_CAL, "My bookings", "Track and manage your appointments",
         lambda: build_booking_history(app), T.SUCCESS),
    ]
    for i in range(len(actions)):
        row.grid_columnconfigure(i, weight=1, uniform="qa")

    for i, (glyph, title, sub, cmd, accent) in enumerate(actions):
        card = C.hover_card(row)
        card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=T.S4, pady=T.S4)
        C.icon_label(inner, glyph, color=accent).pack(anchor="w")
        ctk.CTkLabel(inner, text=title, font=T.F_SMALL_B, text_color=T.TEXT,
                     anchor="w").pack(anchor="w", pady=(T.S3, 0))
        ctk.CTkLabel(inner, text=sub, font=T.F_TINY, text_color=T.TEXT_MUTED,
                     anchor="w", justify="left", wraplength=200,
                     height=30).pack(anchor="w", pady=(2, 0))
        for widget in C._walk(card):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda e, c=cmd: c())


def _upcoming_appointment(scroll, app, bookings):
    C.section_title(scroll, "Upcoming appointment", icon=C.G_CAL)
    upcoming = None
    today = datetime.now().date().isoformat()
    for b in bookings:
        if b["booking_status"] in ("Pending", "Confirmed") and b["appointment_date"] >= today:
            upcoming = b
            break

    card = C.card(scroll)
    card.pack(fill="x", pady=(0, T.S6))

    if upcoming is None:
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=T.S5, pady=T.S5)
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Nothing scheduled yet", font=T.F_H3,
                     text_color=T.TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(left, text="Pick a package and lock in your next session.",
                     font=T.F_SMALL, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")
        C.primary_button(inner, "Book now", lambda: build_package_list(app),
                         width=140, height=40).pack(side="right")
        return

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=T.S5, pady=T.S5)

    left = ctk.CTkFrame(inner, fg_color="transparent")
    left.pack(side="left", anchor="w")
    top_line = ctk.CTkFrame(left, fg_color="transparent")
    top_line.pack(anchor="w")
    ctk.CTkLabel(top_line, text=upcoming["package_name"] or "Tattoo session",
                 font=T.F_H3, text_color=T.TEXT).pack(side="left")
    C.status_badge(top_line, upcoming["booking_status"]).pack(side="left", padx=(T.S3, 0))
    ctk.CTkLabel(left,
                 text="{}  ·  {} - {}".format(upcoming["appointment_date"],
                                              upcoming["start_time"], upcoming["end_time"]),
                 font=T.F_SMALL, text_color=T.TEXT_SEC, anchor="w").pack(anchor="w",
                                                                         pady=(4, 0))
    ctk.CTkLabel(left, text="Artist: {}".format(upcoming["artist_name"] or "TBA"),
                 font=T.F_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")
    ctk.CTkLabel(left, text="Ref {}".format(upcoming["booking_reference"]),
                 font=T.F_MONO, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w",
                                                                         pady=(4, 0))

    right = ctk.CTkFrame(inner, fg_color="transparent")
    right.pack(side="right")
    ctk.CTkLabel(right, text=money(upcoming["total_price"]), font=(T.FAMILY, 20, "bold"),
                 text_color=T.RED).pack(anchor="e")
    C.mk_button(right, "Manage", lambda: build_booking_history(app), kind="secondary",
                width=120, height=38).pack(pady=(T.S3, 0))


def _featured_artists(scroll, app):
    header = ctk.CTkFrame(scroll, fg_color="transparent")
    header.pack(fill="x", pady=(0, T.S3))
    ctk.CTkLabel(header, text="Featured artists", font=T.F_H2, text_color=T.TEXT,
                 anchor="w").pack(side="left")
    C.mk_button(header, "View gallery", lambda: build_gallery(app), kind="ghost",
                width=130, height=32).pack(side="right")

    artists = list(get_active_artists() or [])[:4]
    if not artists:
        C.empty_state(scroll, "no_artists.png", "No artists available",
                      "Our roster is being updated — please check back soon.")
        return

    grid = _responsive_grid(scroll, len(artists), uniform="artist")
    for i, a in enumerate(artists):
        card = C.hover_card(grid)
        card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=T.S4, pady=T.S4)
        _image_label(inner, a["profile_image"], (96, 96),
                     radius=48).pack(anchor="w")
        ctk.CTkLabel(inner, text=a["full_name"], font=T.F_SMALL_B, text_color=T.TEXT,
                     anchor="w").pack(anchor="w", pady=(T.S3, 2))
        ctk.CTkLabel(inner, text=a["specialties"] or "Resident artist", font=T.F_TINY,
                     text_color=T.TEXT_MUTED, anchor="w", justify="left",
                     wraplength=180, height=32).pack(anchor="w")
    ctk.CTkFrame(scroll, height=T.S5, fg_color="transparent").pack()


def _featured_packages(scroll, app, kind="Package"):
    is_tattoo = kind == "Tattoo"
    header = ctk.CTkFrame(scroll, fg_color="transparent")
    header.pack(fill="x", pady=(0, T.S3))
    ctk.CTkLabel(header, text="Featured tattoos" if is_tattoo else "Popular packages",
                 font=T.F_H2, text_color=T.TEXT, anchor="w").pack(side="left")
    C.mk_button(header, "See all", lambda: build_package_list(app, kind=kind),
                kind="ghost", width=100, height=32).pack(side="right")

    items = list(get_active_packages(kind) or [])[:4]
    if not items:
        if is_tattoo:
            C.empty_state(scroll, "no_gallery.png", "No tattoos published yet",
                          "Individual tattoos will appear here once the studio adds them.")
        else:
            C.empty_state(scroll, "no_gallery.png", "No packages yet",
                          "New tattoo packages will appear here once published.")
        return

    grid = _responsive_grid(scroll, 4, uniform="pkg")
    for i, pkg in enumerate(items):
        card = package_card(grid, pkg, app.start_booking,
                            on_view=lambda pid: build_package_details(app, pid),
                            img_size=(260, 150))
        card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))
    ctk.CTkFrame(scroll, height=T.S5, fg_color="transparent").pack()


def _recent_bookings(scroll, app, bookings):
    header = ctk.CTkFrame(scroll, fg_color="transparent")
    header.pack(fill="x", pady=(0, T.S3))
    ctk.CTkLabel(header, text="Recent bookings", font=T.F_H2, text_color=T.TEXT,
                 anchor="w").pack(side="left")
    C.mk_button(header, "View all", lambda: build_booking_history(app), kind="ghost",
                width=100, height=32).pack(side="right")

    if not bookings:
        C.empty_state(scroll, "no_bookings.png", "No bookings yet",
                      "Your first appointment will show up here.",
                      "Browse packages", lambda: build_package_list(app))
        return

    table = C.DataTable(scroll, [
        ("reference", "Reference", 180, "w"),
        ("package", "Design", 220, "w"),
        ("date", "Date", 120, "w"),
        ("time", "Time", 160, "w"),
        ("status", "Status", 130, "w"),
    ], height=min(len(bookings), 5))
    table.pack(fill="x")
    rows = []
    for b in bookings[:5]:
        rows.append(((
            b["booking_reference"],
            b["package_name"] or "-",
            b["appointment_date"],
            "{} - {}".format(b["start_time"], b["end_time"]),
            b["booking_status"],
        ), None))
    table.set_rows(rows)


# ---------------------------------------------------------------------------
# PACKAGE LIST / DETAILS
# ---------------------------------------------------------------------------
def build_package_list(app, term="", category="", kind="Package"):
    is_tattoo = kind == "Tattoo"
    nav_key = "tattoos" if is_tattoo else "packages"
    noun = "tattoos" if is_tattoo else "packages"
    singular = "tattoo" if is_tattoo else "package"

    _begin(app, nav_key)
    if is_tattoo:
        _set_title(app, "Tattoos", "Book an individual tattoo — no package needed")
    else:
        _set_title(app, "Packages", "Find the perfect piece for your next session")
    scroll = _scroll(app)

    bar = C.card(scroll)
    bar.pack(fill="x", pady=(0, T.S5))
    inner = ctk.CTkFrame(bar, fg_color="transparent")
    inner.pack(fill="x", padx=T.S4, pady=T.S4)

    search_wrap, ent_search = C.search_entry(
        inner, "Search {}…".format(noun),
        command=lambda v: _run_search(app, ent_search, cat_var.get(), kind),
        width=260)
    search_wrap.pack(side="left")

    cats = ["All Categories"] + list(get_categories(kind) or [])
    cat_var = ctk.StringVar(value=category if category in cats else "All Categories")
    C.combo(inner, cats, variable=cat_var, width=200).pack(side="left", padx=T.S3)

    C.primary_button(inner, "Search",
                     lambda: _run_search(app, ent_search, cat_var.get(), kind),
                     width=110, height=40).pack(side="left")
    C.mk_button(inner, "Clear", lambda: build_package_list(app, kind=kind),
                kind="secondary", width=90, height=40).pack(side="left", padx=(T.S2, 0))

    if term:
        ent_search.insert(0, term)

    items = (search_packages(term, category, kind) if (term or category)
             else get_active_packages(kind))
    items = list(items or [])

    ctk.CTkLabel(scroll, text="{} {}{}".format(len(items), singular,
                                               "" if len(items) == 1 else "s"),
                 font=T.F_SMALL, text_color=T.TEXT_MUTED, anchor="w").pack(
        anchor="w", pady=(0, T.S4))

    if not items:
        C.empty_state(scroll, "no_gallery.png", "No {} found".format(noun),
                      "Try a different keyword or clear the filters.",
                      "Clear filters", lambda: build_package_list(app, kind=kind))
        return

    grid = _responsive_grid(scroll, 4, uniform="pkg")
    for i, item in enumerate(items):
        r, c = divmod(i, 4)
        card = package_card(grid, item, app.start_booking,
                            on_view=lambda pid: build_package_details(app, pid),
                            img_size=(260, 150))
        card.grid(row=r, column=c, sticky="nsew",
                  padx=(0 if c == 0 else T.S3, 0), pady=(0 if r == 0 else T.S4, 0))


def _run_search(app, entry, category, kind="Package"):
    build_package_list(app, entry.get().strip(),
                       "" if category == "All Categories" else category, kind)


def build_package_details(app, package_id):
    pkg = get_package(package_id)
    if not pkg:
        _begin(app, "packages")
        C.alert_dialog(app, "Not found", "That design is no longer available.", "error")
        build_package_list(app)
        return

    is_tattoo = pkg["kind"] == "Tattoo"
    kind = "Tattoo" if is_tattoo else "Package"
    _begin(app, "tattoos" if is_tattoo else "packages")
    _set_title(app, pkg["package_name"],
               "Tattoo details" if is_tattoo else "Package details")
    scroll = _scroll(app)

    C.mk_button(scroll, "Back to {}".format("tattoos" if is_tattoo else "packages"),
                lambda: build_package_list(app, kind=kind),
                kind="ghost", icon=C.G_BACK, width=200, height=34).pack(anchor="w",
                                                                       pady=(0, T.S4))

    top = ctk.CTkFrame(scroll, fg_color="transparent")
    top.pack(fill="x", pady=(0, T.S5))

    image_wrap = ctk.CTkFrame(top, fg_color=T.CARD, corner_radius=T.RADIUS_LG)
    image_wrap.pack(side="left")
    _image_label(image_wrap, pkg["image_path"], (420, 300),
                 radius=T.RADIUS_LG).pack(padx=2, pady=2)

    info = ctk.CTkFrame(top, fg_color="transparent")
    info.pack(side="left", fill="both", expand=True, padx=(T.S6, 0))

    ctk.CTkLabel(info, text=pkg["category"].upper(), font=T.F_LABEL,
                 text_color=T.RED, anchor="w").pack(anchor="w")
    ctk.CTkLabel(info, text=pkg["package_name"], font=T.F_DISPLAY, text_color=T.TEXT,
                 anchor="w", justify="left", wraplength=520).pack(anchor="w", pady=(4, 8))

    chips = ctk.CTkFrame(info, fg_color="transparent")
    chips.pack(anchor="w", pady=(0, T.S4))
    C.badge(chips, "{} minutes".format(pkg["duration_minutes"]), color=T.INFO).pack(
        side="left")
    C.badge(chips, "Single tattoo" if is_tattoo else "Studio session",
            color=T.TEXT_SEC).pack(side="left", padx=(T.S2, 0))

    price_row = ctk.CTkFrame(info, fg_color="transparent")
    price_row.pack(anchor="w", pady=(T.S3, 0))
    ctk.CTkLabel(price_row, text=money(pkg["price"]), font=(T.FAMILY, 30, "bold"),
                 text_color=T.RED).pack(side="left")
    ctk.CTkLabel(price_row, text="  starting price", font=T.F_TINY,
                 text_color=T.TEXT_MUTED).pack(side="left", pady=(12, 0))

    C.primary_button(info, "Book this {}".format("tattoo" if is_tattoo else "package"),
                     lambda: start_booking_flow(app, package_id),
                     width=220, height=46).pack(anchor="w", pady=(T.S5, 0))

    C.section_title(scroll, "About this design")
    C.card(scroll).pack(fill="x", pady=(0, T.S5))
    desc_card = scroll.winfo_children()[-1]
    ctk.CTkLabel(desc_card, text=pkg["description"] or "No description available.",
                 font=T.F_BODY, text_color=T.TEXT_SEC, anchor="w", justify="left",
                 wraplength=860).pack(anchor="w", padx=T.S5, pady=T.S5)


# ---------------------------------------------------------------------------
# GALLERY
# ---------------------------------------------------------------------------
def build_gallery(app):
    _begin(app, "gallery")
    _set_title(app, "Gallery", "Signature styles from our resident artists")
    scroll = _scroll(app)

    state = {"style": "All"}

    grid_holder = ctk.CTkFrame(scroll, fg_color="transparent")
    grid_holder.pack(fill="both", expand=True)

    def render(style):
        for widget in grid_holder.winfo_children():
            widget.destroy()
        items = [it for it in T.GALLERY_ITEMS
                 if style == "All" or it["style"] == style]
        if not items:
            C.empty_state(grid_holder, "no_gallery.png", "Nothing here yet",
                          "New artwork in this style will appear soon.")
            return
        cols = 3
        grid = _responsive_grid(grid_holder, cols, uniform="gal")
        for i, item in enumerate(items):
            r, c = divmod(i, cols)
            card = C.hover_card(grid)
            card.grid(row=r, column=c, sticky="nsew",
                      padx=(0 if c == 0 else T.S3, 0), pady=(0 if r == 0 else T.S3, 0))
            img_path = os.path.join(T.GALLERY_DIR, item["image"])
            C.CoverImage(card, img_path, height=230, radius=T.RADIUS_LG,
                         bg=T.CARD).pack(fill="x")
            body = ctk.CTkFrame(card, fg_color="transparent")
            body.pack(fill="x", padx=T.S4, pady=T.S4)
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x")
            ctk.CTkLabel(row, text=item["title"], font=T.F_SMALL_B, text_color=T.TEXT,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=item["style"], font=T.F_TINY,
                         text_color=T.RED).pack(side="right")
            ctk.CTkLabel(body, text=item["desc"], font=T.F_TINY, text_color=T.TEXT_MUTED,
                         anchor="w", justify="left", wraplength=280,
                         height=32).pack(anchor="w", pady=(4, 0))

            for widget in C._walk(card):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda e, it=item: gallery_preview(app, it))

    filters = ctk.CTkFrame(scroll, fg_color="transparent")
    filters.pack(fill="x", pady=(0, T.S5))
    C.segmented(filters, T.GALLERY_STYLES, variable=ctk.StringVar(value="All"),
                command=render).pack(anchor="w")

    render("All")


def gallery_preview(app, item):
    dlg = ctk.CTkToplevel(app.root)
    dlg.title(item["title"])
    dlg.configure(fg_color=T.BG)
    dlg.resizable(False, False)
    dlg.transient(app.root)

    img_path = os.path.join(T.GALLERY_DIR, item["image"])
    body = ctk.CTkFrame(dlg, fg_color=T.CARD, corner_radius=T.RADIUS_LG)
    body.pack(fill="both", expand=True, padx=T.S4, pady=T.S4)

    _image_label(body, img_path, (560, 430), radius=T.RADIUS).pack(padx=T.S3,
                                                                  pady=(T.S3, T.S3))
    ctk.CTkLabel(body, text=item["title"], font=T.F_H2, text_color=T.TEXT).pack()
    ctk.CTkLabel(body, text="{}  ·  {}".format(item["style"], item["desc"]),
                 font=T.F_SMALL, text_color=T.TEXT_SEC, wraplength=520,
                 justify="center").pack(pady=(4, T.S3))
    C.mk_button(body, "Close", dlg.destroy, kind="secondary", width=140,
                height=38).pack(pady=(0, T.S4))

    dlg.update_idletasks()
    w, h = 620, 620
    x = app.root.winfo_rootx() + (app.root.winfo_width() - w) // 2
    y = app.root.winfo_rooty() + (app.root.winfo_height() - h) // 3
    dlg.geometry("{}x{}+{}+{}".format(w, h, max(x, 0), max(y, 0)))
    dlg.after(60, lambda: dlg.grab_set())
    dlg.after(80, dlg.lift)


# ---------------------------------------------------------------------------
# BOOKING FLOW
# ---------------------------------------------------------------------------
def _steps_bar(parent, current):
    bar = ctk.CTkFrame(parent, fg_color="transparent")
    bar.pack(fill="x", pady=(0, T.S5))
    for i, name in enumerate(STEPS):
        done = i < current
        active = i == current
        color = T.RED if active else (T.SUCCESS if done else T.ELEVATED)
        text_color = "#FFFFFF" if (active or done) else T.TEXT_MUTED
        chip = ctk.CTkFrame(bar, fg_color="transparent")
        chip.pack(side="left")
        ctk.CTkLabel(chip, text=C.G_CHECK if done else str(i + 1), font=T.F_LABEL,
                     text_color=text_color, fg_color=color, corner_radius=11,
                     width=22, height=22).pack(side="left")
        ctk.CTkLabel(chip, text=name, font=T.F_TINY,
                     text_color=T.TEXT if active else T.TEXT_MUTED).pack(
            side="left", padx=(6, 0))
        if i < len(STEPS) - 1:
            ctk.CTkFrame(bar, width=24, height=2, fg_color=T.BORDER).pack(
                side="left", padx=(T.S2, T.S2))
    return bar


def _booking_header(app, scroll, current, title):
    _steps_bar(scroll, current)
    pkg = app.booking_state["package"]
    head = ctk.CTkFrame(scroll, fg_color="transparent")
    head.pack(fill="x", pady=(0, T.S4))
    left = ctk.CTkFrame(head, fg_color="transparent")
    left.pack(side="left", anchor="w")
    ctk.CTkLabel(left, text=title, font=T.F_H1, text_color=T.TEXT, anchor="w").pack(
        anchor="w")
    ctk.CTkLabel(left, text="{}  ·  {}  ·  {} minutes".format(
        pkg["package_name"], money(pkg["price"]), pkg["duration_minutes"]),
        font=T.F_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")
    C.badge(head, "Step {} of {}".format(min(current + 1, len(STEPS)), len(STEPS)),
            color=T.RED).pack(side="right")


def start_booking_flow(app, package_id):
    pkg = get_package(package_id)
    if not pkg:
        C.alert_dialog(app, "Not found", "That package is no longer available.", "error")
        return
    if not app.current_user:
        app.pending_package_id = package_id
        C.toast(app, "Please sign in to continue booking.", "info")
        app.show_login()
        return

    app.booking_state = {
        "package_id": package_id,
        "package": pkg,
        "artist_id": None,
        "artist": None,
        "date": None,
        "time": None,
        "addons": [],
    }
    build_booking_step_artist(app)


def build_booking_step_artist(app):
    _begin(app, "packages")
    _set_title(app, "Book — Choose artist", "Step 1 of 5")
    scroll = _scroll(app)
    _booking_header(app, scroll, 0, "Choose your artist")

    artists = list(get_active_artists() or [])
    if not artists:
        C.empty_state(scroll, "no_artists.png", "No artists available",
                      "Please try again later or contact the studio.")
        return

    state = app.booking_state
    grid = _responsive_grid(scroll, min(3, len(artists)), uniform="ba")
    cards = []

    def pick(artist):
        state["artist_id"] = artist["artist_id"]
        state["artist"] = artist
        for card, aid in cards:
            selected = aid == artist["artist_id"]
            card.configure(border_color=T.RED if selected else T.BORDER,
                           fg_color=T.RED_SOFT if selected else T.CARD, border_width=2 if selected else 1)
        C.toast(app, "{} selected.".format(artist["full_name"]), "success", 1800)

    for i, a in enumerate(artists):
        r, c = divmod(i, min(3, len(artists)))
        card = ctk.CTkFrame(grid, fg_color=T.CARD, corner_radius=T.RADIUS_LG,
                            border_width=1, border_color=T.BORDER)
        card.grid(row=r, column=c, sticky="nsew",
                  padx=(0 if c == 0 else T.S3, 0), pady=(0 if r == 0 else T.S3, 0))
        cards.append((card, a["artist_id"]))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=T.S5, pady=T.S5)
        _image_label(inner, a["profile_image"], (92, 92), radius=46).pack(anchor="w")
        ctk.CTkLabel(inner, text=a["full_name"], font=T.F_H3, text_color=T.TEXT,
                     anchor="w").pack(anchor="w", pady=(T.S3, 2))
        ctk.CTkLabel(inner, text=a["specialties"] or "Resident artist", font=T.F_TINY,
                     text_color=T.RED, anchor="w", justify="left",
                     wraplength=200).pack(anchor="w")
        ctk.CTkLabel(inner, text=a["bio"] or "", font=T.F_TINY, text_color=T.TEXT_MUTED,
                     anchor="w", justify="left", wraplength=220,
                     height=48).pack(anchor="w", pady=(6, T.S3))
        C.secondary_button(inner, "Select artist", lambda art=a: pick(art),
                           stretch=True, height=38).pack(fill="x")

    bottom = ctk.CTkFrame(scroll, fg_color="transparent")
    bottom.pack(fill="x", pady=T.S5)
    C.mk_button(bottom, "Back", lambda: build_package_details(app, state["package_id"]),
                kind="ghost", icon=C.G_BACK, width=120, height=44).pack(side="left")

    def go_next():
        if not state["artist_id"]:
            C.toast(app, "Please select an artist to continue.", "warning")
            return
        build_booking_step_date(app)

    C.primary_button(bottom, "Continue", go_next, icon=None, width=180,
                     height=44).pack(side="right")


def build_booking_step_date(app):
    _begin(app, "packages")
    _set_title(app, "Book — Choose date", "Step 2 of 5")
    scroll = _scroll(app)
    _booking_header(app, scroll, 1, "Select a date")

    state = app.booking_state
    artist = state["artist"]
    today = datetime.now().date()
    grid = _responsive_grid(scroll, 7, uniform="bd")
    cards = []

    def pick(day):
        state["date"] = day.isoformat()
        for card, dd in cards:
            selected = dd == day
            card.configure(border_color=T.RED if selected else T.BORDER,
                           fg_color=T.RED_SOFT if selected else T.CARD, border_width=2 if selected else 1)

    for i in range(14):
        d = today + timedelta(days=i)
        avail = list(get_availability(artist["artist_id"], d.isoformat()) or [])
        r, c = divmod(i, 7)
        card = ctk.CTkFrame(grid, fg_color=T.CARD, corner_radius=T.RADIUS,
                            border_width=1, border_color=T.BORDER)
        card.grid(row=r, column=c, sticky="nsew",
                  padx=(0 if c == 0 else T.S2, 0), pady=(0 if r == 0 else T.S2, 0))
        cards.append((card, d))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=T.S2, pady=T.S3)
        ctk.CTkLabel(inner, text=d.strftime("%a").upper(), font=T.F_LABEL,
                     text_color=T.TEXT_MUTED).pack()
        ctk.CTkLabel(inner, text=d.strftime("%d"), font=(T.FAMILY, 18, "bold"),
                     text_color=T.TEXT).pack()
        ctk.CTkLabel(inner, text=d.strftime("%b"), font=T.F_TINY,
                     text_color=T.TEXT_SEC).pack()
        dot = T.SUCCESS if avail else T.TEXT_MUTED
        ctk.CTkLabel(inner, text="{} slot{}".format(len(avail), "" if len(avail) == 1 else "s"),
                     font=T.F_TINY, text_color=dot).pack(pady=(4, 0))

        for widget in C._walk(card):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda e, day=d: pick(day))

    bottom = ctk.CTkFrame(scroll, fg_color="transparent")
    bottom.pack(fill="x", pady=T.S5)
    C.mk_button(bottom, "Back", lambda: build_booking_step_artist(app), kind="ghost",
                icon=C.G_BACK, width=120, height=44).pack(side="left")

    def go_next():
        if not state["date"]:
            C.toast(app, "Please pick a date to continue.", "warning")
            return
        build_booking_step_time(app)

    C.primary_button(bottom, "Continue", go_next, width=180, height=44).pack(side="right")


def build_booking_step_time(app):
    _begin(app, "packages")
    _set_title(app, "Book — Choose time", "Step 3 of 5")
    scroll = _scroll(app)
    _booking_header(app, scroll, 2, "Select a time slot")

    state = app.booking_state
    artist = state["artist"]
    date_str = state["date"]
    duration = state["package"]["duration_minutes"]

    ctk.CTkLabel(scroll, text="{}  ·  {}".format(date_str, artist["full_name"]),
                 font=T.F_SMALL, text_color=T.TEXT_SEC, anchor="w").pack(anchor="w",
                                                                        pady=(0, T.S4))

    slots = _available_slots(artist["artist_id"], date_str, duration)
    if not slots:
        C.empty_state(scroll, "no_bookings.png", "No slots on this date",
                      "Pick another day — this artist is fully booked here.",
                      "Choose another date", lambda: build_booking_step_date(app))
        return

    wrap = C.card(scroll)
    wrap.pack(fill="x")
    grid = ctk.CTkFrame(wrap, fg_color="transparent")
    grid.pack(fill="x", padx=T.S4, pady=T.S4)
    cols = 6
    for i in range(cols):
        grid.grid_columnconfigure(i, weight=1, uniform="slot")

    def pick(slot):
        state["time"] = slot
        build_booking_step_details(app)

    for i, slot in enumerate(slots):
        r, c = divmod(i, cols)
        btn = ctk.CTkButton(grid, text=slot, height=44, corner_radius=T.RADIUS,
                            fg_color=T.ELEVATED, hover_color=T.RED,
                            text_color=T.TEXT, font=T.F_SMALL_B,
                            command=lambda s=slot: pick(s))
        btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

    bottom = ctk.CTkFrame(scroll, fg_color="transparent")
    bottom.pack(fill="x", pady=T.S5)
    C.mk_button(bottom, "Back", lambda: build_booking_step_date(app), kind="ghost",
                icon=C.G_BACK, width=120, height=44).pack(side="left")


def _available_slots(artist_id, date_str, duration):
    slots = []
    for av in (get_availability(artist_id, date_str) or []):
        start, end = av["start_time"], av["end_time"]
        t = start
        while True:
            candidate_end = booking_mod.add_minutes(t, duration)
            if candidate_end > end:
                break
            if booking_mod.is_slot_available(artist_id, date_str, t, candidate_end):
                slots.append(t)
            total = (lambda h, m: int(h) * 60 + int(m) + 30)(*t.split(":"))
            t = "{:02d}:{:02d}".format(total // 60, total % 60)
            if total >= (lambda h, m: int(h) * 60 + int(m))(*end.split(":")):
                break
    return slots


def build_booking_step_details(app):
    _begin(app, "packages")
    _set_title(app, "Book — Tattoo details", "Step 4 of 5")
    scroll = _scroll(app)
    _booking_header(app, scroll, 3, "Tell us about your tattoo")

    state = app.booking_state
    form = ctk.CTkFrame(scroll, fg_color="transparent")
    form.pack(fill="x")

    left = ctk.CTkFrame(form, fg_color="transparent")
    left.pack(side="left", fill="both", expand=True, padx=(0, T.S3))
    right = ctk.CTkFrame(form, fg_color="transparent")
    right.pack(side="right", fill="both", expand=True)

    # -- placement
    C.field_label(left, "Placement *").pack(anchor="w")
    placements = booking_mod.get_placement_options()
    placement_var = ctk.StringVar(value=placements[0])
    placement_combo = C.combo(left, placements, variable=placement_var, width=320)
    placement_combo.pack(anchor="w", pady=(0, T.S2))
    custom_wrap, ent_custom = C.labeled_entry(left, None, "Describe your custom placement")
    custom_wrap.pack(fill="x", pady=(0, T.S2))
    custom_wrap.pack_forget()

    def on_placement(choice):
        if choice == "Other":
            custom_wrap.pack(fill="x", pady=(0, T.S2))
        else:
            custom_wrap.pack_forget()

    placement_combo.configure(command=on_placement)

    C.field_label(left, "Size *").pack(anchor="w", pady=(T.S3, 0))
    size_var = ctk.StringVar(value="Medium")
    C.segmented(left, booking_mod.get_size_options(), variable=size_var).pack(anchor="w")

    C.field_label(left, "Reference image (optional)").pack(anchor="w", pady=(T.S4, 6))
    ref_row = ctk.CTkFrame(left, fg_color="transparent")
    ref_row.pack(fill="x")
    ref_label = ctk.CTkLabel(ref_row, text="No image selected", font=T.F_TINY,
                             text_color=T.TEXT_MUTED)
    ref_path = {"value": None}

    def upload():
        f = filedialog.askopenfilename(
            title="Select reference image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if f:
            ref_path["value"] = save_customer_image(f)
            ref_label.configure(text=os.path.basename(f), text_color=T.SUCCESS)

    C.mk_button(ref_row, "Upload image", upload, kind="secondary", icon=C.G_UPLOAD,
                width=160, height=38).pack(side="left")
    ref_label.pack(side="left", padx=(T.S3, 0))

    # -- design + notes
    C.field_label(right, "Design description").pack(anchor="w")
    txt_design = C.text_area(right, height=120)
    txt_design.pack(fill="x", pady=(0, T.S3))

    C.field_label(right, "Additional notes (optional)").pack(anchor="w")
    txt_notes = C.text_area(right, height=80)
    txt_notes.pack(fill="x")

    bottom = ctk.CTkFrame(scroll, fg_color="transparent")
    bottom.pack(fill="x", pady=T.S5)
    C.mk_button(bottom, "Back", lambda: build_booking_step_time(app), kind="ghost",
                icon=C.G_BACK, width=120, height=44).pack(side="left")

    def go_next():
        placement = placement_var.get()
        custom = ent_custom.get().strip()
        if placement == "Other" and not custom:
            C.toast(app, "Please describe your custom placement.", "warning")
            return
        state["placement"] = custom if placement == "Other" else placement
        state["tattoo_size"] = size_var.get()
        state["design_description"] = txt_design.get("1.0", "end-1c").strip()
        state["customer_notes"] = txt_notes.get("1.0", "end-1c").strip()
        state["reference_image_path"] = ref_path["value"]
        build_booking_step_addons(app)

    C.primary_button(bottom, "Continue", go_next, width=180, height=44).pack(side="right")


def save_customer_image(src_path):
    os.makedirs(REF_IMG_DIR, exist_ok=True)
    ext = os.path.splitext(src_path)[1]
    name = "ref_{}{}".format(uuid.uuid4().hex[:8], ext.lower())
    dst = os.path.join(REF_IMG_DIR, name)
    shutil.copy2(src_path, dst)
    return dst.replace("\\", "/")


def build_booking_step_addons(app):
    _begin(app, "packages")
    _set_title(app, "Book — Add-ons", "Step 5 of 5")
    scroll = _scroll(app)
    _booking_header(app, scroll, 4, "Optional extras")

    addons = list(get_addons() or [])
    if not addons:
        ctk.CTkLabel(scroll, text="No add-on services are currently offered.",
                     font=T.F_SMALL, text_color=T.TEXT_MUTED).pack(anchor="w")

    selections = {}

    grid = ctk.CTkFrame(scroll, fg_color="transparent")
    grid.pack(fill="x")
    for i in range(3):
        grid.grid_columnconfigure(i, weight=1, uniform="addon")

    for i, a in enumerate(addons):
        r, c = divmod(i, 3)
        card = C.card(grid)
        card.grid(row=r, column=c, sticky="nsew",
                  padx=(0 if c == 0 else T.S3, 0), pady=(0 if r == 0 else T.S3, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=T.S4, pady=T.S4)

        ctk.CTkLabel(inner, text=a["addon_name"], font=T.F_SMALL_B, text_color=T.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(inner, text=a["description"] or "", font=T.F_TINY,
                     text_color=T.TEXT_MUTED, anchor="w", justify="left",
                     wraplength=240, height=32).pack(anchor="w", pady=(2, T.S2))
        ctk.CTkLabel(inner, text="+ {}".format(money(a["price"])), font=T.F_SMALL_B,
                     text_color=T.RED, anchor="w").pack(anchor="w")

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(T.S3, 0))
        var = ctk.IntVar(value=0)
        qty = ctk.IntVar(value=1)
        C.checkbox(row, "Add", variable=var).pack(side="left")
        stepper = ctk.CTkFrame(row, fg_color="transparent")
        stepper.pack(side="right")
        ctk.CTkLabel(stepper, text="Qty", font=T.F_TINY,
                     text_color=T.TEXT_MUTED).pack(side="left", padx=(0, 4))
        ctk.CTkButton(stepper, text="−", width=26, height=26, corner_radius=6,
                      fg_color=T.ELEVATED, hover_color=T.RED, text_color=T.TEXT,
                      command=lambda q=qty: q.set(max(1, q.get() - 1))).pack(side="left")
        ctk.CTkLabel(stepper, textvariable=qty, font=T.F_SMALL_B, text_color=T.TEXT,
                     width=26).pack(side="left")
        ctk.CTkButton(stepper, text="+", width=26, height=26, corner_radius=6,
                      fg_color=T.ELEVATED, hover_color=T.RED, text_color=T.TEXT,
                      command=lambda q=qty: q.set(q.get() + 1)).pack(side="left")

        selections[a["addon_id"]] = (var, qty, a)

    bottom = ctk.CTkFrame(scroll, fg_color="transparent")
    bottom.pack(fill="x", pady=T.S5)
    C.mk_button(bottom, "Back", lambda: build_booking_step_details(app), kind="ghost",
                icon=C.G_BACK, width=120, height=44).pack(side="left")

    def go_next():
        chosen = []
        for addon_id, (var, qty, a) in selections.items():
            if var.get() == 1:
                chosen.append({"addon_id": addon_id, "quantity": int(qty.get()),
                               "unit_price": a["price"]})
        app.booking_state["addons"] = chosen
        build_booking_summary(app)

    C.primary_button(bottom, "Review booking", go_next, width=200,
                     height=44).pack(side="right")


def build_booking_summary(app):
    _begin(app, "packages")
    _set_title(app, "Review booking", "Confirm your appointment")
    scroll = _scroll(app)
    _steps_bar(scroll, 5)

    state = app.booking_state
    pkg = state["package"]
    artist = state["artist"]

    outer = ctk.CTkFrame(scroll, fg_color="transparent")
    outer.pack(fill="x")
    outer.grid_columnconfigure(0, weight=3, uniform="sum")
    outer.grid_columnconfigure(1, weight=2, uniform="sum")

    left = C.card(outer)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, T.S3))
    inner = ctk.CTkFrame(left, fg_color="transparent")
    inner.pack(fill="x", padx=T.S5, pady=T.S5)

    ctk.CTkLabel(inner, text="Appointment details", font=T.F_H2,
                 text_color=T.TEXT, anchor="w").pack(anchor="w", pady=(0, T.S3))

    rows = [
        (C.G_IMAGE, "Tattoo" if pkg["kind"] == "Tattoo" else "Package",
         pkg["package_name"]),
        (C.G_STAR, "Artist", artist["full_name"]),
        (C.G_CAL, "Date", state["date"]),
        (C.G_CLOCK, "Time", "{} - {}".format(
            state["time"], booking_mod.add_minutes(state["time"], pkg["duration_minutes"]))),
        (C.G_DOT, "Placement", state.get("placement", "-")),
        (C.G_DOT, "Size", state.get("tattoo_size", "-")),
    ]
    for glyph, label, value in rows:
        line = ctk.CTkFrame(inner, fg_color="transparent")
        line.pack(fill="x", pady=3)
        ctk.CTkLabel(line, text=glyph + "  " + label, font=T.F_SMALL,
                     text_color=T.TEXT_MUTED, width=140, anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=str(value), font=T.F_SMALL_B, text_color=T.TEXT,
                     anchor="w", justify="left", wraplength=420).pack(side="left")

    if state.get("design_description"):
        C.divider(inner, pady=T.S3)
        ctk.CTkLabel(inner, text="Design brief", font=T.F_LABEL,
                     text_color=T.TEXT_SEC, anchor="w").pack(anchor="w")
        ctk.CTkLabel(inner, text=state["design_description"], font=T.F_SMALL,
                     text_color=T.TEXT, anchor="w", justify="left",
                     wraplength=520).pack(anchor="w", pady=(2, 0))

    right = C.card(outer)
    right.grid(row=0, column=1, sticky="nsew")
    rinner = ctk.CTkFrame(right, fg_color="transparent")
    rinner.pack(fill="x", padx=T.S5, pady=T.S5)

    ctk.CTkLabel(rinner, text="Price breakdown", font=T.F_H2, text_color=T.TEXT,
                 anchor="w").pack(anchor="w", pady=(0, T.S3))

    def price_line(label, amount, muted=False, bold=False):
        line = ctk.CTkFrame(rinner, fg_color="transparent")
        line.pack(fill="x", pady=3)
        ctk.CTkLabel(line, text=label, font=T.F_BODY_B if bold else T.F_SMALL,
                     text_color=T.TEXT_MUTED if muted else T.TEXT,
                     anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=money(amount),
                     font=(T.FAMILY, 13, "bold") if bold else T.F_SMALL,
                     text_color=T.RED if bold else T.TEXT).pack(side="right")

    price_line("Base price", pkg["price"])

    addon_total = 0.0
    for a in state.get("addons", []):
        amount = float(a["unit_price"]) * int(a["quantity"])
        addon_total += amount
        price_line("{} × {}".format(a["quantity"], get_addon_name(a["addon_id"])), amount,
                   muted=True)

    C.divider(rinner, pady=T.S3)
    total = float(pkg["price"]) + addon_total
    price_line("Total", total, bold=True)

    note = ctk.CTkFrame(rinner, fg_color=T.RED_SOFT, corner_radius=T.RADIUS)
    note.pack(fill="x", pady=(T.S4, 0))
    ctk.CTkLabel(note, text="Deposit & final payment are handled in-studio. "
                            "No online payment is taken.",
                 font=T.F_TINY, text_color=T.TEXT_SEC, wraplength=260,
                 justify="left").pack(padx=T.S3, pady=T.S3)

    bottom = ctk.CTkFrame(scroll, fg_color="transparent")
    bottom.pack(fill="x", pady=T.S5)
    C.mk_button(bottom, "Back", lambda: build_booking_step_addons(app), kind="ghost",
                icon=C.G_BACK, width=140, height=46).pack(side="left")
    C.primary_button(bottom, "Confirm booking", lambda: confirm_booking(app, total),
                     width=220, height=46).pack(side="right")


def get_addon_name(addon_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT addon_name FROM package_addons WHERE addon_id = ?", (addon_id,))
        row = cur.fetchone()
        return row["addon_name"] if row else "Add-on"
    finally:
        conn.close()


def confirm_booking(app, total=None):
    state = app.booking_state
    loading = C.LoadingOverlay(app.content_frame, "Confirming your booking…")
    loading.place(x=0, y=0, relwidth=1, relheight=1)
    loading.lift()

    def run():
        ok, msg, booking_id, reference = booking_mod.create_booking_flight(
            app.current_user["user_id"], state["package_id"], state["artist_id"],
            state["date"], state["time"], state.get("placement", ""),
            state.get("tattoo_size", ""), state.get("design_description", ""),
            state.get("reference_image_path"), state.get("customer_notes", ""),
            state.get("addons", []))
        loading.stop()
        if ok:
            app.last_booking_id = booking_id
            app.last_booking_reference = reference
            build_booking_confirmation(app)
            C.toast(app, "Booking confirmed — reference {}.".format(reference), "success")
        else:
            C.alert_dialog(app, "Booking failed", msg, "error")

    app.root.after(500, run)


def build_booking_confirmation(app):
    _begin(app, "bookings")
    _set_title(app, "Booking confirmed", "Your appointment is locked in")
    scroll = _scroll(app)

    state = app.booking_state
    pkg = state["package"]
    artist = state["artist"]
    total = float(pkg["price"]) + sum(
        float(a["unit_price"]) * int(a["quantity"]) for a in state.get("addons", []))

    hero = ctk.CTkFrame(scroll, fg_color=T.SURFACE, corner_radius=T.RADIUS_LG,
                        height=150)
    hero.pack(fill="x", pady=(0, T.S5))
    hero.pack_propagate(False)

    def paint(canvas, w, h):
        canvas.create_text(w / 2, h * 0.36, text=C.G_CHECK, fill=T.SUCCESS,
                           font=(T.FAMILY, 34, "bold"))
        canvas.create_text(w / 2, h * 0.68, text="Your tattoo appointment is booked.",
                           fill=T.TEXT, font=(T.FAMILY, 16, "bold"))

    C.CoverImage(hero, T.BANNER_ARTIST, radius=T.RADIUS_LG, darken=0.55,
                 bg=T.SURFACE, overlay=paint).place(x=0, y=0, relwidth=1, relheight=1)

    card = C.card(scroll)
    card.pack(fill="x")
    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=T.S6, pady=T.S6)

    ctk.CTkLabel(inner, text="BOOKING REFERENCE", font=T.F_LABEL,
                 text_color=T.TEXT_MUTED).pack(anchor="w")
    ctk.CTkLabel(inner, text=app.last_booking_reference or "-", font=(T.FAMILY, 24, "bold"),
                 text_color=T.RED).pack(anchor="w", pady=(2, T.S5))

    for label, value in [
        ("Tattoo" if pkg["kind"] == "Tattoo" else "Package", pkg["package_name"]),
        ("Artist", artist["full_name"]),
        ("Date", state["date"]),
        ("Time", "{} - {}".format(state["time"],
                                  booking_mod.add_minutes(state["time"],
                                                          pkg["duration_minutes"]))),
        ("Placement", state.get("placement", "-")),
        ("Total", money(total)),
    ]:
        line = ctk.CTkFrame(inner, fg_color="transparent")
        line.pack(fill="x", pady=4)
        ctk.CTkLabel(line, text=label, font=T.F_SMALL, text_color=T.TEXT_MUTED,
                     width=140, anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=str(value), font=T.F_SMALL_B, text_color=T.TEXT,
                     anchor="w").pack(side="left")

    ctk.CTkLabel(inner, text="Keep this reference to track or discuss your appointment.",
                 font=T.F_TINY, text_color=T.TEXT_MUTED).pack(anchor="w", pady=(T.S4, 0))

    row = ctk.CTkFrame(scroll, fg_color="transparent")
    row.pack(fill="x", pady=T.S5)
    C.primary_button(row, "View my bookings", lambda: build_booking_history(app),
                     width=200, height=46).pack(side="left")
    C.mk_button(row, "Back home", lambda: build_home(app), kind="secondary",
                width=160, height=46).pack(side="left", padx=(T.S3, 0))
    C.mk_button(row, "Book another", lambda: build_package_list(app), kind="ghost",
                width=160, height=46).pack(side="left", padx=(T.S3, 0))


# ---------------------------------------------------------------------------
# BOOKING HISTORY
# ---------------------------------------------------------------------------
def build_booking_history(app):
    _begin(app, "bookings")
    _set_title(app, "My bookings", "Track and manage your appointments")
    scroll = _scroll(app)

    bookings = list(get_bookings_by_user(app.current_user["user_id"]) or [])
    if not bookings:
        C.empty_state(scroll, "no_bookings.png", "No bookings yet",
                      "Once you book an appointment it will appear here.",
                      "Browse packages", lambda: build_package_list(app))
        return

    counts = {}
    for b in bookings:
        counts[b["booking_status"]] = counts.get(b["booking_status"], 0) + 1

    stats = ctk.CTkFrame(scroll, fg_color="transparent")
    stats.pack(fill="x", pady=(0, T.S5))
    cards = [
        ("Total", len(bookings), T.RED),
        ("Pending", counts.get("Pending", 0), T.WARNING),
        ("Confirmed", counts.get("Confirmed", 0), T.INFO),
        ("Completed", counts.get("Completed", 0), T.SUCCESS),
    ]
    for i, (label, value, accent) in enumerate(cards):
        stats.grid_columnconfigure(i, weight=1, uniform="bstats")
        C.stat_card(stats, C.G_CAL, label, value, accent=accent).grid(
            row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))

    table = C.DataTable(scroll, [
        ("id", "ID", 60, "center"),
        ("reference", "Reference", 180, "w"),
        ("package", "Design", 200, "w"),
        ("artist", "Artist", 160, "w"),
        ("date", "Date", 110, "w"),
        ("time", "Time", 150, "w"),
        ("status", "Status", 120, "w"),
    ], height=14)
    table.pack(fill="both", expand=True)

    rows = []
    for b in bookings:
        rows.append(((
            b["booking_id"], b["booking_reference"], b["package_name"] or "-",
            b["artist_name"] or "-", b["appointment_date"],
            "{} - {}".format(b["start_time"], b["end_time"]), b["booking_status"],
        ), None))
    table.set_rows(rows)

    actions = ctk.CTkFrame(scroll, fg_color="transparent")
    actions.pack(fill="x", pady=(T.S4, 0))
    C.primary_button(actions, "Cancel selected", lambda: _cancel_selected(app, table),
                     kind="danger", width=190, height=42).pack(side="left")
    C.primary_button(actions, "New booking", lambda: build_package_list(app),
                     width=170, height=42).pack(side="left", padx=(T.S3, 0))


def _cancel_selected(app, table):
    values = table.selected_values()
    if not values:
        C.toast(app, "Select a booking first.", "warning")
        return
    reference, status = values[1], values[6]
    if status != "Pending":
        C.toast(app, "Only pending bookings can be cancelled.", "warning")
        return

    def do_cancel():
        booking = get_booking_by_reference(reference)
        if not booking:
            C.toast(app, "Booking not found.", "error")
            return
        ok, msg = booking_mod.cancel_my_booking(booking["booking_id"],
                                                app.current_user["user_id"])
        if ok:
            C.toast(app, "Booking cancelled.", "success")
            build_booking_history(app)
        else:
            C.toast(app, msg, "error")

    C.confirm_dialog(app, "Cancel booking",
                     "Cancel booking {}? This cannot be undone.".format(reference),
                     do_cancel, confirm_text="Cancel booking", kind="danger",
                     cancel_text="Keep booking")


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------
def build_profile(app):
    _begin(app, "profile")
    _set_title(app, "Profile", "Your studio account")
    scroll = _scroll(app)

    user = app.current_user or {}
    bookings = list(get_bookings_by_user(user.get("user_id", -1)) or [])
    upcoming = [b for b in bookings
                if b["booking_status"] in ("Pending", "Confirmed")
                and b["appointment_date"] >= datetime.now().date().isoformat()]

    header = C.card(scroll)
    header.pack(fill="x", pady=(0, T.S5))
    inner = ctk.CTkFrame(header, fg_color="transparent")
    inner.pack(fill="x", padx=T.S6, pady=T.S6)

    C.avatar(inner, initials(user.get("full_name")), size=72, accent=T.RED,
             font=(T.FAMILY, 22, "bold")).pack(side="left")
    texts = ctk.CTkFrame(inner, fg_color="transparent")
    texts.pack(side="left", padx=(T.S5, 0))
    ctk.CTkLabel(texts, text=user.get("full_name", "Guest"), font=T.F_H1,
                 text_color=T.TEXT, anchor="w").pack(anchor="w")
    ctk.CTkLabel(texts, text="Customer account", font=T.F_SMALL,
                 text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")
    C.badge(texts, "{} bookings".format(len(bookings)), color=T.INFO).pack(anchor="w",
                                                                          pady=(6, 0))

    C.mk_button(inner, "Log out", app.logout, kind="danger", icon=C.G_LOGOUT,
                width=130, height=42).pack(side="right")

    stats = ctk.CTkFrame(scroll, fg_color="transparent")
    stats.pack(fill="x", pady=(0, T.S5))
    tiles = [
        (C.G_CAL, "Total bookings", len(bookings), T.RED),
        (C.G_CLOCK, "Upcoming", len(upcoming), T.INFO),
        (C.G_STAR, "Completed",
         len([b for b in bookings if b["booking_status"] == "Completed"]), T.SUCCESS),
    ]
    for i, (glyph, label, value, accent) in enumerate(tiles):
        stats.grid_columnconfigure(i, weight=1, uniform="pstats")
        C.stat_card(stats, glyph, label, value, accent=accent).grid(
            row=0, column=i, sticky="nsew", padx=(0 if i == 0 else T.S3, 0))

    C.section_title(scroll, "Account details")
    details = C.card(scroll)
    details.pack(fill="x", pady=(0, T.S5))
    dinner = ctk.CTkFrame(details, fg_color="transparent")
    dinner.pack(fill="x", padx=T.S5, pady=T.S5)

    fields = [
        ("First name", user.get("first_name")),
        ("Middle name", user.get("middle_name")),
        ("Last name", user.get("last_name")),
        ("Email", user.get("email")),
        ("Phone", user.get("phone")),
    ]
    for label, value in fields:
        line = ctk.CTkFrame(dinner, fg_color="transparent")
        line.pack(fill="x", pady=5)
        ctk.CTkLabel(line, text=label, font=T.F_SMALL, text_color=T.TEXT_MUTED,
                     width=150, anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=str(value) if value else "—", font=T.F_BODY_B,
                     text_color=T.TEXT, anchor="w").pack(side="left")

    actions = ctk.CTkFrame(scroll, fg_color="transparent")
    actions.pack(fill="x")
    C.primary_button(actions, "My bookings", lambda: build_booking_history(app),
                     width=170, height=44).pack(side="left")
    C.mk_button(actions, "Browse packages", lambda: build_package_list(app),
                kind="secondary", width=180, height=44).pack(side="left", padx=(T.S3, 0))
