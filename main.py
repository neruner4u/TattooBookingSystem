"""Inkognito Studios — Booking System.

Application shell: authentication, sidebar navigation and screen routing.
"""
import tkinter as tk

import customtkinter as ctk

import theme as T
import components as C
import database
import auth
import customer
import admin

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BRAND_TOP = "INKOGNITO"
BRAND_BOTTOM = "STUDIOS"
TAGLINE = "Premium tattoo artistry, private studios, and effortless booking."


class App:
    """Root application controller."""

    def __init__(self, root):
        self.root = root
        self.root.title("Inkognito Studios — Booking System")
        self.root.minsize(1160, 720)
        try:
            self.root.state("zoomed")           # start maximised (full screen)
        except tk.TclError:
            self.root.geometry("1440x900")
        self.root.configure(fg_color=T.BG)

        # session state
        self.current_user = None
        self.current_admin = None
        self.is_admin_mode = False
        self.login_mode = "customer"          # customer | admin
        self.title_clicks = 0
        self.click_timer = None
        self.last_booking_id = None
        self.last_booking_reference = None
        self.image_refs = []
        self.pending_package_id = None

        # shell widgets
        self.sidebar = None
        self.topbar = None
        self.top_title = None
        self.top_subtitle = None
        self.content_frame = None
        self.nav_items = {}

        database.init_database()
        self.show_login()

    # ------------------------------------------------------------------ utils
    def clear_content(self):
        if self.content_frame is None:
            return
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.image_refs = []

    def _reset_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.sidebar = self.topbar = self.top_title = self.top_subtitle = None
        self.content_frame = None
        self.nav_items = {}
        self.image_refs = []

    # ------------------------------------------------------------------ login
    def show_login(self):
        self._reset_root()
        self.root.configure(fg_color=T.BG)

        left = ctk.CTkFrame(self.root, fg_color=T.SIDEBAR, corner_radius=0)
        left.pack(side="left", fill="both", expand=True)

        panel_width = 540
        right = ctk.CTkFrame(self.root, fg_color=T.BG, corner_radius=0, width=panel_width)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        def draw_brand(canvas, w, h):
            pad = int(w * 0.10)
            top = int(h * 0.30)
            canvas.create_line(pad, top - 58, pad + 64, top - 58, fill=T.RED, width=4,
                               tags="brand")
            canvas.create_text(pad, top, anchor="w", text=BRAND_TOP, fill=T.TEXT,
                               font=(T.FAMILY, 44, "bold"), tags="brand")
            canvas.create_text(pad, top + 46, anchor="w", text=BRAND_BOTTOM, fill=T.RED,
                               font=(T.FAMILY, 44, "bold"), tags="brand")
            canvas.create_text(pad, top + 108, anchor="w", text=TAGLINE, fill=T.TEXT_SEC,
                               font=(T.FAMILY, 13), width=w - 2 * pad, tags="brand")
            canvas.create_text(pad, h - 54, anchor="w",
                               text="EST. 2014   ·   PRIVATE STUDIOS   ·   AWARD WINNING ARTISTS",
                               fill=T.TEXT_MUTED, font=(T.FAMILY, 10), tags="brand")

        cover = C.CoverImage(left, T.AUTH_IMG, scrim="left", scrim_strength=0.93,
                             overlay=draw_brand, bg=T.SIDEBAR)
        cover.place(x=0, y=0, relwidth=1, relheight=1)

        form_wrap = ctk.CTkFrame(right, fg_color="transparent")
        form_wrap.place(relx=0.5, rely=0.5, anchor="center", relwidth=1)

        if self.login_mode == "admin":
            self._build_admin_login(form_wrap)
        else:
            self._build_customer_login(form_wrap)

    def _build_customer_login(self, parent):
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.pack(padx=T.S8, fill="x")

        ctk.CTkLabel(card, text="Welcome back", font=T.F_DISPLAY, text_color=T.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(card, text="Sign in to manage your tattoo appointments.",
                     font=T.F_SMALL, text_color=T.TEXT_MUTED, anchor="w").pack(
            anchor="w", pady=(4, T.S6))

        name_wrap, ent_user = C.labeled_entry(card, "Email or phone", "you@example.com")
        name_wrap.pack(fill="x", pady=(0, T.S4))
        pass_wrap, ent_pass = C.password_entry(card, "Password", "Your password")
        pass_wrap.pack(fill="x", pady=(0, T.S2))

        error_lbl = ctk.CTkLabel(card, text="", font=T.F_TINY, text_color=T.RED, anchor="w")
        error_lbl.pack(anchor="w", pady=(T.S2, 0))

        def do_login():
            user = ent_user.get().strip()
            pwd = ent_pass.get()
            if not user or not pwd:
                error_lbl.configure(text="Please enter your email/phone and password.")
                return
            error_lbl.configure(text="")
            loading = C.LoadingOverlay(self.root, "Signing you in…")
            loading.place(x=0, y=0, relwidth=1, relheight=1)
            loading.lift()

            def run():
                ok, res = auth.customer_login(user, pwd)
                loading.stop()
                if ok:
                    self.current_user = res
                    self.is_admin_mode = False
                    self.finish_login()
                    C.toast(self, "Welcome back, {}!".format(res["first_name"]), "success")
                else:
                    error_lbl.configure(text=res)
                    C.toast(self, res, "error")

            self.root.after(400, run)

        ent_pass.bind("<Return>", lambda e: do_login())
        ent_user.bind("<Return>", lambda e: do_login())

        C.primary_button(card, "Sign In", do_login, stretch=True, height=46).pack(
            fill="x", pady=(T.S5, T.S4))

        C.divider(card, pady=T.S2)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", pady=(T.S4, 0))
        ctk.CTkLabel(row, text="New to the studio?", font=T.F_SMALL,
                     text_color=T.TEXT_MUTED).pack(side="left")
        C.mk_button(row, "Create account", self.show_register, kind="ghost",
                    width=140, height=32).pack(side="right")

        C.mk_button(card, "Admin sign in", self.toggle_login_mode, kind="ghost",
                    width=140, height=30, icon=C.G_SHIELD).pack(anchor="w", pady=(T.S5, 0))

    def _build_admin_login(self, parent):
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.pack(padx=T.S8, fill="x")

        ctk.CTkLabel(card, text="Admin access", font=T.F_DISPLAY, text_color=T.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(card, text="Studio administrator sign-in.", font=T.F_SMALL,
                     text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(4, T.S6))

        u_wrap, ent_user = C.labeled_entry(card, "Username", "admin")
        u_wrap.pack(fill="x", pady=(0, T.S4))
        p_wrap, ent_pass = C.password_entry(card, "Password", "Your password")
        p_wrap.pack(fill="x")

        error_lbl = ctk.CTkLabel(card, text="", font=T.F_TINY, text_color=T.RED, anchor="w")
        error_lbl.pack(anchor="w", pady=(T.S3, 0))

        def do_login():
            username = ent_user.get().strip()
            pwd = ent_pass.get()
            if not username or not pwd:
                error_lbl.configure(text="Please enter username and password.")
                return
            ok, res = auth.admin_login(username, pwd)
            if ok:
                self.current_admin = res
                self.is_admin_mode = True
                self.finish_login()
                C.toast(self, "Admin session started.", "success")
            else:
                error_lbl.configure(text=res)
                C.toast(self, res, "error")

        ent_pass.bind("<Return>", lambda e: do_login())
        C.primary_button(card, "Sign In", do_login, stretch=True, height=46).pack(
            fill="x", pady=(T.S5, T.S4))
        C.divider(card, pady=T.S2)
        C.mk_button(card, "Back to customer sign in", self.toggle_login_mode, kind="ghost",
                    width=220, height=32, icon=C.G_LOGOUT).pack(anchor="w", pady=(T.S4, 0))

    # -------------------------------------------------------------- register
    def show_register(self):
        self._reset_root()
        self.root.configure(fg_color=T.BG)

        left = ctk.CTkFrame(self.root, fg_color=T.SIDEBAR, corner_radius=0)
        left.pack(side="left", fill="both", expand=True)

        def draw_brand(canvas, w, h):
            pad = int(w * 0.10)
            top = int(h * 0.30)
            canvas.create_line(pad, top - 58, pad + 64, top - 58, fill=T.RED, width=4,
                               tags="brand")
            canvas.create_text(pad, top, anchor="w", text="JOIN", fill=T.TEXT,
                               font=(T.FAMILY, 44, "bold"), tags="brand")
            canvas.create_text(pad, top + 46, anchor="w", text="INKOGNITO", fill=T.RED,
                               font=(T.FAMILY, 44, "bold"), tags="brand")
            canvas.create_text(pad, top + 108, anchor="w",
                               text="Create an account to book artists, track appointments "
                                    "and save your favourite designs.",
                               fill=T.TEXT_SEC, font=(T.FAMILY, 13), width=w - 2 * pad,
                               tags="brand")

        cover = C.CoverImage(left, T.AUTH_IMG, scrim="left", scrim_strength=0.93,
                             overlay=draw_brand, bg=T.SIDEBAR)
        cover.place(x=0, y=0, relwidth=1, relheight=1)

        right = ctk.CTkFrame(self.root, fg_color=T.BG, corner_radius=0, width=560)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        scroll = C.scroll_area(right)
        scroll.pack(fill="both", expand=True, padx=T.S8, pady=T.S7)

        ctk.CTkLabel(scroll, text="Create your account", font=T.F_H1, text_color=T.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(scroll, text="It only takes a moment.", font=T.F_SMALL,
                     text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(3, T.S5))

        f_first, e_first = C.labeled_entry(scroll, "First name *", "Jane")
        f_first.pack(fill="x", pady=(0, T.S3))
        f_mid, e_mid = C.labeled_entry(scroll, "Middle name", "Optional")
        f_mid.pack(fill="x", pady=(0, T.S3))
        f_last, e_last = C.labeled_entry(scroll, "Last name *", "Doe")
        f_last.pack(fill="x", pady=(0, T.S3))
        f_email, e_email = C.labeled_entry(scroll, "Email", "you@example.com")
        f_email.pack(fill="x", pady=(0, T.S3))
        f_phone, e_phone = C.labeled_entry(scroll, "Phone", "+63 900 000 0000")
        f_phone.pack(fill="x", pady=(0, T.S3))
        f_pass, e_pass = C.password_entry(scroll, "Password *", "Minimum 6 characters")
        f_pass.pack(fill="x", pady=(0, T.S3))
        f_confirm, e_confirm = C.password_entry(scroll, "Confirm password *",
                                                "Re-enter your password")
        f_confirm.pack(fill="x", pady=(0, T.S2))

        ctk.CTkLabel(scroll, text="Provide at least an email or a phone number.",
                     font=T.F_TINY, text_color=T.TEXT_MUTED, anchor="w").pack(anchor="w")

        error_lbl = ctk.CTkLabel(scroll, text="", font=T.F_TINY, text_color=T.RED, anchor="w")
        error_lbl.pack(anchor="w", pady=(T.S2, 0))

        def do_register():
            if e_pass.get() != e_confirm.get():
                error_lbl.configure(text="Passwords do not match.")
                C.toast(self, "Passwords do not match.", "error")
                return
            ok, msg = auth.customer_register(
                e_first.get().strip(),
                e_mid.get().strip() or None,
                e_last.get().strip(),
                e_email.get().strip() or None,
                e_phone.get().strip() or None,
                e_pass.get())
            if ok:
                C.toast(self, "Account created — please sign in.", "success")
                self.login_mode = "customer"
                self.show_login()
            else:
                error_lbl.configure(text=msg)
                C.toast(self, msg, "error")

        C.primary_button(scroll, "Create Account", do_register, stretch=True,
                         height=46).pack(fill="x", pady=(T.S5, T.S3))
        C.mk_button(scroll, "Back to sign in", self.show_login, kind="secondary",
                    stretch=True, height=40).pack(fill="x", pady=(0, T.S4))

    def toggle_login_mode(self):
        self.login_mode = "admin" if self.login_mode == "customer" else "customer"
        self.title_clicks = 0
        self.show_login()

    # -------------------------------------------------------------- post login
    def finish_login(self):
        self._reset_root()
        self.root.configure(fg_color=T.BG)

        self.sidebar = ctk.CTkFrame(self.root, fg_color=T.SIDEBAR, corner_radius=0,
                                    width=T.SIDEBAR_W)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        main = ctk.CTkFrame(self.root, fg_color=T.BG, corner_radius=0)
        main.pack(side="right", fill="both", expand=True)

        self._build_topbar(main)

        self.content_frame = ctk.CTkFrame(main, fg_color=T.BG, corner_radius=0)
        self.content_frame.pack(fill="both", expand=True, padx=T.S6, pady=(0, T.S6))

        if self.is_admin_mode:
            self._build_sidebar_admin()
            admin.build_dashboard(self)
        else:
            self._build_sidebar_customer()
            customer.build_home(self)

    def _build_topbar(self, parent):
        self.topbar = ctk.CTkFrame(parent, fg_color=T.BG, corner_radius=0, height=T.TOPBAR_H)
        self.topbar.pack(fill="x", padx=T.S6, pady=(T.S5, T.S3))
        self.topbar.pack_propagate(False)

        title_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        title_box.pack(side="left", anchor="w")
        self.top_title = ctk.CTkLabel(title_box, text="Home", font=T.F_H1, text_color=T.TEXT,
                                      anchor="w")
        self.top_title.pack(anchor="w")
        self.top_subtitle = ctk.CTkLabel(title_box, text="", font=T.F_TINY,
                                         text_color=T.TEXT_MUTED, anchor="w")
        self.top_subtitle.pack(anchor="w")

        actions = ctk.CTkFrame(self.topbar, fg_color="transparent")
        actions.pack(side="right", anchor="e")

        if self.is_admin_mode:
            person = self.current_admin or {}
            name = person.get("full_name", "Administrator")
            role = "Administrator"
            initials = "".join(p[0] for p in name.split()[:2]).upper() or "A"
            accent = T.GOLD
        else:
            person = self.current_user or {}
            name = person.get("full_name") or person.get("first_name", "Guest")
            role = "Customer"
            initials = "".join(p[0] for p in name.split()[:2]).upper() or "U"
            accent = T.RED

        chip = ctk.CTkFrame(actions, fg_color=T.ELEVATED, corner_radius=T.RADIUS_PILL)
        chip.pack(side="right")
        inner = ctk.CTkFrame(chip, fg_color="transparent")
        inner.pack(padx=T.S3, pady=T.S2)

        ctk.CTkLabel(inner, text=initials, font=T.F_SMALL_B, text_color="#FFFFFF",
                     fg_color=accent, corner_radius=18, width=36, height=36).pack(side="left")
        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left", padx=(T.S3, T.S2))
        ctk.CTkLabel(text_box, text=name, font=T.F_SMALL_B, text_color=T.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(text_box, text=role, font=T.F_TINY, text_color=T.TEXT_MUTED,
                     anchor="w").pack(anchor="w")

        C.mk_button(actions, "Logout", self.logout, kind="secondary", width=110,
                    height=40, icon=C.G_LOGOUT).pack(side="right", padx=(0, T.S3))

    # -------------------------------------------------------------- sidebars
    def _sidebar_header(self):
        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", padx=T.S5, pady=(T.S6, T.S5))
        ctk.CTkLabel(header, text="INKOGNITO", font=(T.FAMILY, 18, "bold"), text_color=T.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(header, text="STUDIOS", font=(T.FAMILY, 18, "bold"), text_color=T.RED,
                     anchor="w").pack(anchor="w", pady=(0, 0))
        line = ctk.CTkFrame(header, height=2, fg_color=T.RED, corner_radius=1, width=46)
        line.pack(anchor="w", pady=(T.S3, 0))

    def _build_nav_section(self, label, items):
        if label:
            ctk.CTkLabel(self.sidebar, text=label.upper(), font=T.F_LABEL,
                         text_color=T.TEXT_MUTED, anchor="w").pack(
                fill="x", padx=T.S6, pady=(T.S4, T.S2))
        for key, text, icon, command in items:
            item = C.NavItem(self.sidebar, text, command, icon=icon, key=key)
            item.pack(fill="x", padx=T.S3, pady=1)
            self.nav_items[key] = item

    def _build_sidebar_customer(self):
        self._sidebar_header()
        self._build_nav_section("Menu", [
            ("home", "Home", C.G_HOME, self.nav_click),
            ("packages", "Packages", C.G_GRID, self.nav_click),
            ("tattoos", "Tattoos", C.G_PEN, self.nav_click),
            ("gallery", "Gallery", C.G_GALLERY, self.nav_click),
            ("bookings", "My Bookings", C.G_CAL, self.nav_click),
            ("profile", "Profile", C.G_USER, self.nav_click),
        ])
        self._sidebar_footer("Book your next\nappointment today",
                             "Book Now", lambda: customer.build_package_list(self))

    def _build_sidebar_admin(self):
        self._sidebar_header()
        self._build_nav_section("Overview", [
            ("dashboard", "Dashboard", C.G_GRID, self.admin_nav_click),
        ])
        self._build_nav_section("Manage", [
            ("packages", "Packages", C.G_IMAGE, self.admin_nav_click),
            ("tattoos", "Tattoos", C.G_PEN, self.admin_nav_click),
            ("artists", "Artists", C.G_STAR, self.admin_nav_click),
            ("availability", "Availability", C.G_CLOCK, self.admin_nav_click),
            ("addons", "Add-ons", C.G_PLUS, self.admin_nav_click),
        ])
        self._build_nav_section("Operations", [
            ("bookings", "Bookings", C.G_CAL, self.admin_nav_click),
            ("payments", "Payments", C.G_CASH, self.admin_nav_click),
            ("customers", "Customers", C.G_USER, self.admin_nav_click),
        ])

    def _sidebar_footer(self, message, button_text, command):
        footer = ctk.CTkFrame(self.sidebar, fg_color=T.CARD, corner_radius=T.RADIUS)
        footer.pack(side="bottom", fill="x", padx=T.S3, pady=T.S4)
        inner = ctk.CTkFrame(footer, fg_color="transparent")
        inner.pack(fill="x", padx=T.S4, pady=T.S4)
        ctk.CTkLabel(inner, text=message, font=T.F_TINY, text_color=T.TEXT_SEC,
                     justify="left", anchor="w").pack(anchor="w")
        C.primary_button(inner, button_text, command, stretch=True,
                         height=36).pack(fill="x", pady=(T.S3, 0))

    # ------------------------------------------------------------------- nav
    def set_active_nav(self, key):
        for k, item in self.nav_items.items():
            item.set_active(k == key)

    def nav_click(self, key):
        self.set_active_nav(key)
        if key == "home":
            customer.build_home(self)
        elif key == "packages":
            customer.build_package_list(self)
        elif key == "tattoos":
            customer.build_package_list(self, kind="Tattoo")
        elif key == "gallery":
            customer.build_gallery(self)
        elif key == "bookings":
            customer.build_booking_history(self)
        elif key == "profile":
            customer.build_profile(self)

    def admin_nav_click(self, key):
        self.set_active_nav(key)
        if key == "dashboard":
            admin.build_dashboard(self)
        elif key == "packages":
            admin.build_package_manager(self)
        elif key == "tattoos":
            admin.build_tattoo_manager(self)
        elif key == "artists":
            admin.build_artist_manager(self)
        elif key == "availability":
            admin.build_availability_manager(self)
        elif key == "addons":
            admin.build_addon_manager(self)
        elif key == "bookings":
            admin.build_booking_manager(self)
        elif key == "payments":
            admin.build_payment_manager(self)
        elif key == "customers":
            admin.build_customer_manager(self)

    def start_booking(self, package_id):
        customer.start_booking_flow(self, package_id)

    def logout(self):
        self.current_user = None
        self.current_admin = None
        self.is_admin_mode = False
        self.login_mode = "customer"
        self.show_login()
        C.toast(self, "You have been signed out.", "info")


def main():
    root = ctk.CTk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
