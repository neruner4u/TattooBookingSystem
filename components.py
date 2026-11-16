"""Reusable UI components shared across every screen.

All widgets are built on top of CustomTkinter so they inherit rounded
corners, hover states and dark-mode theming for free.
"""
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

import theme as T

# ---------------------------------------------------------------------------
# Glyphs (kept to characters well supported by Segoe UI)
# ---------------------------------------------------------------------------
G_HOME = "⌂"
G_GRID = "▦"
G_GALLERY = "▧"
G_CAL = "▤"
G_USER = "◍"
G_STAR = "✦"
G_CLOCK = "◷"
G_PLUS = "＋"
G_GEAR = "⚙"
G_CASH = "₱"
G_LOGOUT = "⇦"
G_CLOSE = "✕"
G_CHECK = "✓"
G_WARN = "⚠"
G_INFO = "ⓘ"
G_ARROW = "▸"
G_DOT = "●"
G_SHIELD = "◆"
G_PEN = "✎"
G_TRASH = "🗑"
G_IMAGE = "▣"
G_SEARCH = "⌕"
G_FILTER = "≡"
G_SORT = "⇅"
G_REFRESH = "↻"
G_BACK = "←"
G_NEXT = "→"
G_UPLOAD = "⇧"
G_LOGO = "✒"

TOAST_STYLES = {
    "success": (T.SUCCESS_SOFT, T.SUCCESS, G_CHECK),
    "error": (T.DANGER_SOFT, T.RED, G_WARN),
    "warning": (T.WARNING_SOFT, T.WARNING, G_WARN),
    "info": (T.INFO_SOFT, T.INFO, G_INFO),
}


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
def mk_button(parent, text, command=None, kind="primary", icon=None,
              width=None, height=40, radius=T.RADIUS, font=None,
              font_small=False, stretch=False, **kwargs):
    """Create a themed button.

    kind: primary | secondary | ghost | danger | success | gold
    """
    presets = {
        "primary":   dict(fg_color=T.RED, hover_color=T.RED_HOVER, text_color=T.TEXT_ON_RED,
                          border_width=0),
        "secondary": dict(fg_color=T.ELEVATED, hover_color=T.ELEVATED_HI, text_color=T.TEXT,
                          border_width=1, border_color=T.BORDER),
        "ghost":     dict(fg_color="transparent", hover_color=T.ELEVATED, text_color=T.TEXT_SEC,
                          border_width=0),
        "danger":    dict(fg_color="transparent", hover_color=T.DANGER_SOFT, text_color=T.RED,
                          border_width=1, border_color=T.CRIMSON),
        "success":   dict(fg_color=T.SUCCESS_SOFT, hover_color="#1B3D2B", text_color=T.SUCCESS,
                          border_width=1, border_color="#1F4D36"),
        "gold":      dict(fg_color=T.GOLD, hover_color="#DCB63D", text_color="#1A1409",
                          border_width=0),
    }
    preset = presets.get(kind, presets["primary"])
    preset.update(kwargs)
    label = "{}  {}".format(icon, text).strip() if icon else text
    btn = ctk.CTkButton(
        parent,
        text=label,
        command=command,
        width=width or (40 if stretch else 140),
        height=height,
        corner_radius=radius,
        font=font or (T.F_BUTTON_SM if font_small else T.F_BUTTON),
        **preset
    )
    if stretch:
        btn.pack(fill="x")
    return btn


def primary_button(parent, text, command, **kw):
    return mk_button(parent, text, command, kind="primary", **kw)


def secondary_button(parent, text, command, **kw):
    return mk_button(parent, text, command, kind="secondary", **kw)


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------
def card(parent, radius=T.RADIUS_LG, fg=None, border=None, **kw):
    return ctk.CTkFrame(
        parent,
        corner_radius=radius,
        fg_color=fg or T.CARD,
        border_width=1 if border is not False else 0,
        border_color=border or T.BORDER,
        **kw
    )


def scroll_area(parent, fg="transparent"):
    return ctk.CTkScrollableFrame(
        parent, fg_color=fg, corner_radius=0,
        scrollbar_button_color=T.ELEVATED, scrollbar_button_hover_color=T.RED)


def divider(parent, pady=0):
    line = ctk.CTkFrame(parent, height=1, fg_color=T.BORDER_SOFT, corner_radius=0)
    line.pack(fill="x", pady=pady)
    return line


def section_title(parent, title, subtitle=None, icon=None, pady=(0, T.S3)):
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    wrap.pack(fill="x", pady=pady)
    label = "{}  {}".format(icon, title) if icon else title
    ctk.CTkLabel(wrap, text=label, font=T.F_H2, text_color=T.TEXT,
                 anchor="w").pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(wrap, text=subtitle, font=T.F_SMALL, text_color=T.TEXT_MUTED,
                     anchor="w").pack(anchor="w", pady=(2, 0))
    return wrap


def page_header(parent, title, subtitle=None, icon=None):
    """Standard page header with optional right-aligned actions container."""
    head = ctk.CTkFrame(parent, fg_color="transparent")
    head.pack(fill="x", pady=(0, T.S5))
    left = ctk.CTkFrame(head, fg_color="transparent")
    left.pack(side="left", anchor="w")
    label = "{}   {}".format(icon, title) if icon else title
    ctk.CTkLabel(left, text=label, font=T.F_H1, text_color=T.TEXT, anchor="w").pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(left, text=subtitle, font=T.F_SMALL, text_color=T.TEXT_MUTED,
                     anchor="w").pack(anchor="w", pady=(3, 0))
    actions = ctk.CTkFrame(head, fg_color="transparent")
    actions.pack(side="right", anchor="e")
    return actions


def badge(parent, text, color=T.RED, text_color=T.TEXT, solid=False, size=None):
    return ctk.CTkLabel(
        parent, text=text,
        font=size or T.F_LABEL,
        text_color=text_color if solid else color,
        fg_color=color if solid else T.ELEVATED,
        corner_radius=T.RADIUS_PILL,
        padx=10, pady=3,
    )


def status_badge(parent, status):
    palette = {
        "Pending":   (T.WARNING, T.WARNING_SOFT),
        "Confirmed": (T.INFO, T.INFO_SOFT),
        "Completed": (T.SUCCESS, T.SUCCESS_SOFT),
        "Cancelled": (T.TEXT_MUTED, T.ELEVATED),
        "Rejected":  (T.RED, T.DANGER_SOFT),
        "Paid":      (T.SUCCESS, T.SUCCESS_SOFT),
        "Failed":    (T.RED, T.DANGER_SOFT),
        "Refunded":  (T.GOLD, T.WARNING_SOFT),
    }
    fg, bg = palette.get(status, (T.TEXT_SEC, T.ELEVATED))
    return ctk.CTkLabel(parent, text=status, font=T.F_LABEL, text_color=fg,
                        fg_color=bg, corner_radius=T.RADIUS_PILL, padx=12, pady=4)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def _focus_highlight(entry):
    """Turn the entry border red while focused."""
    entry.bind("<FocusIn>", lambda e: entry.configure(border_color=T.RED), add="+")
    entry.bind("<FocusOut>", lambda e: entry.configure(border_color=T.BORDER), add="+")


def labeled_entry(parent, label=None, placeholder="", show=None, height=44):
    """Return ``(wrapper, entry)`` — wrapper is packed by the caller."""
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    if label:
        ctk.CTkLabel(wrap, text=label, font=T.F_LABEL, text_color=T.TEXT_SEC,
                     anchor="w").pack(anchor="w", pady=(0, 6))
    entry = ctk.CTkEntry(wrap, placeholder_text=placeholder, height=height,
                         corner_radius=T.RADIUS, fg_color=T.ELEVATED, border_width=1,
                         border_color=T.BORDER, text_color=T.TEXT,
                         placeholder_text_color=T.TEXT_MUTED, font=T.F_BODY, show=show)
    entry.pack(fill="x")
    _focus_highlight(entry)
    return wrap, entry


def password_entry(parent, label=None, placeholder="Your password", height=44):
    """Password field with a show/hide toggle. Returns ``(wrapper, entry)``."""
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    if label:
        ctk.CTkLabel(wrap, text=label, font=T.F_LABEL, text_color=T.TEXT_SEC,
                     anchor="w").pack(anchor="w", pady=(0, 6))
    row = ctk.CTkFrame(wrap, fg_color="transparent")
    row.pack(fill="x")

    entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=height,
                         corner_radius=T.RADIUS, fg_color=T.ELEVATED, border_width=1,
                         border_color=T.BORDER, text_color=T.TEXT,
                         placeholder_text_color=T.TEXT_MUTED, font=T.F_BODY, show="•")
    entry.pack(side="left", fill="x", expand=True)
    _focus_highlight(entry)

    state = {"hidden": True}

    def toggle():
        state["hidden"] = not state["hidden"]
        entry.configure(show="•" if state["hidden"] else "")
        btn.configure(text="Show" if state["hidden"] else "Hide")

    btn = ctk.CTkButton(row, text="Show", width=64, height=height,
                        corner_radius=T.RADIUS, fg_color=T.ELEVATED,
                        hover_color=T.ELEVATED_HI, text_color=T.TEXT_SEC,
                        font=T.F_TINY, command=toggle)
    btn.pack(side="right", padx=(T.S2, 0))
    return wrap, entry


def search_entry(parent, placeholder="Search…", command=None, width=240):
    """A rounded search field with a leading glyph. Returns ``(wrapper, entry)``."""
    wrap = ctk.CTkFrame(parent, fg_color=T.ELEVATED, corner_radius=T.RADIUS,
                        border_width=1, border_color=T.BORDER)
    ctk.CTkLabel(wrap, text=G_SEARCH, font=(T.FAMILY, 13), text_color=T.TEXT_MUTED,
                 width=22).pack(side="left", padx=(T.S3, 0))
    entry = ctk.CTkEntry(wrap, placeholder_text=placeholder, height=40, width=width,
                         corner_radius=0, border_width=0, fg_color="transparent",
                         text_color=T.TEXT, placeholder_text_color=T.TEXT_MUTED,
                         font=T.F_BODY)
    entry.pack(side="left", fill="x", expand=True, padx=(0, T.S3))
    if command is not None:
        entry.bind("<Return>", lambda e: command(entry.get().strip()))
    return wrap, entry


def combo(parent, values, variable=None, width=200, command=None, height=40):
    return ctk.CTkComboBox(
        parent, values=list(values), variable=variable, width=width, height=height,
        corner_radius=T.RADIUS, fg_color=T.ELEVATED, border_width=1,
        border_color=T.BORDER, button_color=T.ELEVATED, button_hover_color=T.RED,
        dropdown_fg_color=T.CARD, dropdown_hover_color=T.RED_SOFT,
        dropdown_text_color=T.TEXT, dropdown_font=T.F_SMALL,
        text_color=T.TEXT, font=T.F_BODY, command=command)


def segmented(parent, values, variable=None, command=None, height=38, width=None):
    seg = ctk.CTkSegmentedButton(
        parent, values=list(values), variable=variable, command=command,
        font=T.F_SMALL_B, fg_color=T.ELEVATED, selected_color=T.RED,
        selected_hover_color=T.RED_HOVER, unselected_color=T.ELEVATED,
        unselected_hover_color=T.ELEVATED_HI, text_color=T.TEXT,
        corner_radius=T.RADIUS_PILL, height=height)
    if width:
        seg.configure(width=width)
    return seg


def text_area(parent, height=110, font=None):
    return ctk.CTkTextbox(parent, height=height, corner_radius=T.RADIUS,
                          fg_color=T.ELEVATED, border_width=1, border_color=T.BORDER,
                          text_color=T.TEXT, font=font or T.F_BODY, wrap="word")


def checkbox(parent, text, variable=None, command=None):
    return ctk.CTkCheckBox(parent, text=text, variable=variable, command=command,
                           font=T.F_SMALL, text_color=T.TEXT, fg_color=T.RED,
                           hover_color=T.RED_HOVER, border_color=T.BORDER,
                           checkmark_color=T.TEXT_ON_RED, corner_radius=4,
                           checkbox_width=20, checkbox_height=20)


def avatar(parent, initials, size=36, accent=T.RED, font=None):
    return ctk.CTkLabel(parent, text=initials, font=font or T.F_SMALL_B,
                        text_color="#FFFFFF", fg_color=accent, corner_radius=size // 2,
                        width=size, height=size)


def field_label(parent, text, pady=(0, 6)):
    return ctk.CTkLabel(parent, text=text, font=T.F_LABEL, text_color=T.TEXT_SEC,
                        anchor="w")


# ---------------------------------------------------------------------------
# Responsive cover image (canvas based, fills and crops on resize)
# ---------------------------------------------------------------------------
class CoverImage(tk.Canvas):
    """A canvas that always fills itself with a cover-cropped image.

    ``overlay`` is an optional callable ``fn(canvas, width, height)`` invoked
    after every re-render, which lets screens draw text or graphics on top of
    the photo while keeping them crisp at any window size.
    """

    def __init__(self, parent, image_path=None, radius=0, darken=0.0, scrim=None,
                 scrim_strength=0.9, bg=T.CARD, overlay=None, gradient=None, **kw):
        super().__init__(parent, highlightthickness=0, bd=0, bg=bg, **kw)
        self._src = None if gradient else T.open_source(image_path)
        self._gradient = gradient
        self._radius = radius
        self._darken = darken
        self._scrim = scrim
        self._scrim_strength = scrim_strength
        self._bg = bg
        self._overlay = overlay
        self._token = None
        self._last_size = (0, 0)
        self._photo = None
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        size = (event.width, event.height)
        if size == self._last_size or size[0] < 4 or size[1] < 4:
            return
        self._last_size = size
        if self._token:
            self.after_cancel(self._token)
        self._token = self.after(30, self._render)

    def _render(self):
        w, h = self._last_size
        if w < 4 or h < 4:
            return
        if self._gradient:
            start, end = self._gradient[0], self._gradient[1]
            horizontal = (self._gradient[2] != "vertical") if len(self._gradient) > 2 else True
            img = T.linear_gradient((w, h), start, end, horizontal=horizontal)
        else:
            img = T.cover_crop(self._src, (w, h))
        if self._darken:
            img = T.darkened(img, self._darken)
        if self._scrim:
            layer, mask = T.gradient_scrim((w, h), self._scrim, self._scrim_strength)
            img = Image.composite(layer, img, mask)
        if self._radius:
            img = T.rounded(img, self._radius)
        else:
            img = img.convert("RGB")
        self._photo = ImageTk.PhotoImage(img)
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self._photo)
        if self._overlay:
            try:
                self._overlay(self, w, h)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Sidebar navigation item
# ---------------------------------------------------------------------------
class NavItem(ctk.CTkFrame):
    def __init__(self, parent, text, command, icon=None, key=None):
        super().__init__(parent, fg_color="transparent", corner_radius=T.RADIUS)
        self.key = key
        self.command = command
        self._active = False
        self.configure(cursor="hand2")

        self.bar = ctk.CTkFrame(self, width=3, height=22, corner_radius=2,
                                fg_color="transparent")
        self.bar.pack(side="left", padx=(5, 0))
        self.bar.pack_propagate(False)

        label = "{}   {}".format(icon, text) if icon else text
        self.btn = ctk.CTkButton(
            self, text=label, anchor="w", height=42, corner_radius=T.RADIUS,
            fg_color="transparent", hover_color=T.ELEVATED, text_color=T.TEXT_SEC,
            font=T.F_SMALL_B, command=self._clicked)
        self.btn.pack(side="left", fill="x", expand=True, padx=(4, 8), pady=2)

        for widget in (self, self.btn):
            widget.bind("<Enter>", self._hover_in)
            widget.bind("<Leave>", self._hover_out)

    def _clicked(self):
        if callable(self.command):
            self.command(self.key)

    def _hover_in(self, _=None):
        if not self._active:
            self.btn.configure(text_color=T.TEXT)

    def _hover_out(self, _=None):
        if not self._active:
            self.btn.configure(text_color=T.TEXT_SEC)

    def set_active(self, active):
        self._active = bool(active)
        if active:
            self.configure(fg_color=T.RED_SOFT)
            self.bar.configure(fg_color=T.RED)
            self.btn.configure(text_color=T.TEXT, fg_color="transparent",
                               hover_color=T.RED_SOFT)
        else:
            self.configure(fg_color="transparent")
            self.bar.configure(fg_color="transparent")
            self.btn.configure(text_color=T.TEXT_SEC, fg_color="transparent",
                               hover_color=T.ELEVATED)


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------
def empty_state(parent, image_name, title, message, action_text=None, action_command=None,
                height=200):
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    wrap.pack(expand=True, fill="both", pady=T.S6)

    import os
    path = os.path.join(T.EMPTY_DIR, image_name)
    img = T.photo(path, (min(height * 2, 420), height), mode="contain")
    if img:
        ctk.CTkLabel(wrap, image=img, text="").pack(pady=(0, T.S4))

    ctk.CTkLabel(wrap, text=title, font=T.F_H2, text_color=T.TEXT).pack()
    ctk.CTkLabel(wrap, text=message, font=T.F_SMALL, text_color=T.TEXT_MUTED,
                 wraplength=420, justify="center").pack(pady=(6, T.S4))
    if action_text and action_command:
        primary_button(wrap, action_text, action_command, width=200).pack()
    return wrap


# ---------------------------------------------------------------------------
# Loading overlay
# ---------------------------------------------------------------------------
class LoadingOverlay(ctk.CTkFrame):
    def __init__(self, parent, text="Loading…"):
        super().__init__(parent, fg_color=T.BG, corner_radius=0)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        self.bar = ctk.CTkProgressBar(inner, width=220, height=6, corner_radius=3,
                                      progress_color=T.RED, fg_color=T.ELEVATED)
        self.bar.pack(pady=(0, T.S4))
        self.bar.set(0)
        ctk.CTkLabel(inner, text=text, font=T.F_SMALL, text_color=T.TEXT_SEC).pack()
        self._value = 0.0
        self._animating = True
        self._animate()

    def _animate(self):
        if not self.winfo_exists() or not self._animating:
            return
        self._value += 0.04
        if self._value > 1:
            self._value = 0
        try:
            self.bar.set(self._value)
        except Exception:
            return
        self.after(40, self._animate)

    def stop(self):
        self._animating = False
        self.destroy()


def show_loading(app, text="Working…", duration=900, then=None):
    overlay = LoadingOverlay(app.content_frame, text)
    overlay.place(x=0, y=0, relwidth=1, relheight=1)
    overlay.lift()

    def finish():
        try:
            overlay.stop()
        except Exception:
            pass
        if then:
            then()

    app.root.after(duration, finish)
    return overlay


# ---------------------------------------------------------------------------
# Toasts
# ---------------------------------------------------------------------------
_toasts = []


def _layout_toasts(root):
    y = T.S6
    for toast_frame in _toasts:
        try:
            toast_frame.place_configure(relx=1.0, rely=0.0, x=-T.S6, y=y, anchor="ne")
            toast_frame.update_idletasks()
            y += toast_frame.winfo_reqheight() + T.S2
        except Exception:
            continue


def toast(app, message, kind="info", duration=3400):
    root = app.root
    bg, accent, glyph = TOAST_STYLES.get(kind, TOAST_STYLES["info"])
    frame = ctk.CTkFrame(root, corner_radius=T.RADIUS, fg_color=T.ELEVATED,
                         border_width=1, border_color=accent)
    inner = ctk.CTkFrame(frame, fg_color="transparent")
    inner.pack(padx=T.S4, pady=T.S3)
    ctk.CTkLabel(inner, text=glyph, font=T.F_BUTTON, text_color=accent,
                 width=22).pack(side="left", padx=(0, T.S3))
    ctk.CTkLabel(inner, text=message, font=T.F_SMALL, text_color=T.TEXT,
                 wraplength=320, justify="left").pack(side="left")
    _toasts.append(frame)
    _layout_toasts(root)

    def close():
        if frame in _toasts:
            _toasts.remove(frame)
        try:
            frame.destroy()
        except Exception:
            pass
        _layout_toasts(root)

    frame.bind("<Button-1>", lambda e: close())
    for child in inner.winfo_children():
        child.bind("<Button-1>", lambda e: close())
    root.after(duration, close)
    return frame


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------
def _center(window, parent, width, height):
    parent.update_idletasks()
    try:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 3
    except Exception:
        x, y = 300, 200
    window.geometry("{}x{}+{}+{}".format(width, height, max(x, 0), max(y, 0)))


def confirm_dialog(app, title, message, on_confirm, confirm_text="Confirm",
                   kind="primary", cancel_text="Cancel"):
    dlg = ctk.CTkToplevel(app.root)
    dlg.title(title)
    dlg.configure(fg_color=T.BG)
    dlg.resizable(False, False)
    dlg.transient(app.root)
    _center(dlg, app.root, 440, 220)

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=T.S6, pady=T.S5)

    head = ctk.CTkFrame(body, fg_color="transparent")
    head.pack(fill="x")
    ctk.CTkLabel(head, text=G_WARN if kind != "danger" else G_TRASH,
                 font=(T.FAMILY, 22), text_color=T.RED if kind == "danger" else T.GOLD,
                 width=34).pack(side="left", padx=(0, T.S3))
    ctk.CTkLabel(head, text=title, font=T.F_H2, text_color=T.TEXT,
                 anchor="w").pack(side="left")

    ctk.CTkLabel(body, text=message, font=T.F_SMALL, text_color=T.TEXT_SEC,
                 wraplength=360, justify="left").pack(anchor="w", pady=(T.S3, T.S6))

    actions = ctk.CTkFrame(body, fg_color="transparent")
    actions.pack(fill="x", side="bottom")

    def do_confirm():
        dlg.grab_release()
        dlg.destroy()
        if on_confirm:
            on_confirm()

    mk_button(actions, cancel_text, dlg.destroy, kind="secondary", width=120,
              height=38).pack(side="right")
    mk_button(actions, confirm_text, do_confirm,
              kind="danger" if kind == "danger" else "primary",
              width=140, height=38).pack(side="right", padx=(0, T.S3))

    dlg.after(60, lambda: dlg.grab_set())
    dlg.after(80, dlg.lift)
    return dlg


def alert_dialog(app, title, message, kind="info", on_close=None):
    dlg = ctk.CTkToplevel(app.root)
    dlg.title(title)
    dlg.configure(fg_color=T.BG)
    dlg.resizable(False, False)
    dlg.transient(app.root)
    _center(dlg, app.root, 420, 200)

    accent = {"info": T.INFO, "success": T.SUCCESS, "error": T.RED,
              "warning": T.WARNING}.get(kind, T.INFO)
    glyph = {"info": G_INFO, "success": G_CHECK, "error": G_WARN,
             "warning": G_WARN}.get(kind, G_INFO)

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=T.S6, pady=T.S5)

    head = ctk.CTkFrame(body, fg_color="transparent")
    head.pack(fill="x")
    ctk.CTkLabel(head, text=glyph, font=(T.FAMILY, 22), text_color=accent,
                 width=34).pack(side="left", padx=(0, T.S3))
    ctk.CTkLabel(head, text=title, font=T.F_H2, text_color=T.TEXT, anchor="w").pack(side="left")

    ctk.CTkLabel(body, text=message, font=T.F_SMALL, text_color=T.TEXT_SEC,
                 wraplength=340, justify="left").pack(anchor="w", pady=(T.S3, T.S5))

    def close():
        dlg.grab_release()
        dlg.destroy()
        if on_close:
            on_close()

    mk_button(body, "OK", close, kind="primary", width=120, height=38).pack(side="right")
    dlg.after(60, lambda: dlg.grab_set())
    dlg.after(80, dlg.lift)
    return dlg


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
_tables_styled = False


def style_tables():
    global _tables_styled
    if _tables_styled:
        return
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure("Tattoo.Treeview",
                    background=T.CARD, fieldbackground=T.CARD, foreground=T.TEXT,
                    rowheight=40, borderwidth=0, relief="flat", font=T.F_SMALL)
    style.configure("Tattoo.Treeview.Heading",
                    background=T.ELEVATED, foreground=T.TEXT_SEC, relief="flat",
                    borderwidth=0, padding=(10, 8), font=T.F_LABEL)
    style.map("Tattoo.Treeview",
              background=[("selected", T.RED)],
              foreground=[("selected", "#FFFFFF")])
    style.map("Tattoo.Treeview.Heading",
              background=[("active", T.ELEVATED_HI)],
              foreground=[("active", T.TEXT)])
    try:
        style.layout("Tattoo.Treeview", [("Tattoo.Treeview.treearea", {"sticky": "nswe"})])
    except Exception:
        pass

    style.configure("Tattoo.Vertical.TScrollbar",
                    background=T.ELEVATED, troughcolor=T.CARD, bordercolor=T.CARD,
                    arrowcolor=T.TEXT_SEC, relief="flat", borderwidth=0)
    style.map("Tattoo.Vertical.TScrollbar",
              background=[("active", T.RED)])
    _tables_styled = True


class DataTable(ctk.CTkFrame):
    """A dark themed treeview with scrollbar and click-to-sort headings."""

    def __init__(self, parent, columns, height=14, sortable=True, fg=T.CARD, **kw):
        super().__init__(parent, fg_color=fg, corner_radius=T.RADIUS,
                         border_width=1, border_color=T.BORDER, **kw)
        style_tables()
        self.columns = columns  # list of (key, heading, width, anchor)
        self.sortable = sortable
        self._rows = []
        self._sort_key = None
        self._sort_desc = False

        ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(self, columns=ids, show="headings",
                                 style="Tattoo.Treeview", height=height)
        for key, heading, width, anchor in columns:
            heading_kw = {"text": heading}
            if sortable:
                heading_kw["command"] = lambda k=key: self._sort_by(k)
            self.tree.heading(key, **heading_kw)
            self.tree.column(key, width=width, anchor=anchor, stretch=True)
        self.tree.tag_configure("odd", background=T.CARD)
        self.tree.tag_configure("even", background=T.SURFACE)

        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview,
                                    style="Tattoo.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=self.scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        self.scroll.pack(side="right", fill="y", padx=(0, 2), pady=2)

    # -- data ---------------------------------------------------------------
    def set_rows(self, rows):
        """rows: list of (values_tuple, tag_or_None)."""
        self._rows = list(rows)
        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = self._rows
        if self._sort_key is not None:
            idx = [c[0] for c in self.columns].index(self._sort_key)

            def sort_val(row):
                val = row[0][idx]
                try:
                    return (0, float(str(val).replace("$", "").replace(",", "").strip()))
                except Exception:
                    return (1, str(val).lower())

            rows = sorted(rows, key=sort_val, reverse=self._sort_desc)

        for i, (values, tag) in enumerate(rows):
            zebra = "even" if i % 2 else "odd"
            tags = (zebra,) if not tag else (zebra, tag)
            self.tree.insert("", "end", values=values, tags=tags)

    def _sort_by(self, key):
        if self._sort_key == key:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_key = key
            self._sort_desc = False
        arrow = "  ▾" if self._sort_desc else "  ▴"
        for ckey, heading, _w, _a in self.columns:
            base = heading.rstrip(" ▴▾")
            self.tree.heading(ckey, text=base + (arrow if ckey == key else ""))
        self._refresh()

    def selected_values(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])["values"]

    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())


# ---------------------------------------------------------------------------
# Cards used on dashboards
# ---------------------------------------------------------------------------
def stat_card(parent, icon, label, value, accent=T.RED, sub=None):
    frame = card(parent, fg=T.CARD)
    inner = ctk.CTkFrame(frame, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=T.S5, pady=T.S5)

    top = ctk.CTkFrame(inner, fg_color="transparent")
    top.pack(fill="x")
    ico = ctk.CTkLabel(top, text=icon, font=(T.FAMILY, 18), text_color=accent,
                       fg_color=T.ELEVATED, corner_radius=T.RADIUS, width=38, height=38)
    ico.pack(side="left")
    texts = ctk.CTkFrame(top, fg_color="transparent")
    texts.pack(side="left", padx=(T.S3, 0), fill="x", expand=True)
    ctk.CTkLabel(texts, text=str(value), font=(T.FAMILY, 22, "bold"), text_color=T.TEXT,
                 anchor="w").pack(anchor="w")
    ctk.CTkLabel(texts, text=label, font=T.F_TINY, text_color=T.TEXT_MUTED,
                 anchor="w").pack(anchor="w")
    if sub:
        ctk.CTkLabel(inner, text=sub, font=T.F_TINY, text_color=T.TEXT_SEC,
                     anchor="w").pack(anchor="w", pady=(T.S2, 0))
    return frame


def hover_card(parent, normal=T.CARD, hover=T.CARD_HOVER, **kw):
    """A card that brightens on hover."""
    frame = card(parent, fg=normal, **kw)
    enable_hover(frame, normal, hover)
    return frame


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        for item in _walk(child):
            yield item


def enable_hover(frame, normal, hover):
    """Recursively bind hover recolouring to a card and all its children."""
    def on_enter(_):
        try:
            frame.configure(fg_color=hover)
        except Exception:
            pass

    def on_leave(_):
        try:
            frame.configure(fg_color=normal)
        except Exception:
            pass

    for widget in _walk(frame):
        widget.bind("<Enter>", on_enter, add="+")
        widget.bind("<Leave>", on_leave, add="+")


def icon_label(parent, glyph, size=18, color=T.RED, box=True, box_size=38,
               fg=T.ELEVATED):
    """A glyph inside an optional rounded tile."""
    if box:
        return ctk.CTkLabel(parent, text=glyph, font=(T.FAMILY, size), text_color=color,
                            fg_color=fg, corner_radius=T.RADIUS, width=box_size,
                            height=box_size)
    return ctk.CTkLabel(parent, text=glyph, font=(T.FAMILY, size), text_color=color)


def image_label(parent, path, size, radius=T.RADIUS, fallback="No image", mode="cover"):
    """A label showing a cover-cropped image, or a themed placeholder."""
    img = T.photo(path, size, mode=mode, radius=radius)
    if img is None:
        return ctk.CTkLabel(parent, text=fallback, font=T.F_TINY,
                            text_color=T.TEXT_MUTED, fg_color=T.ELEVATED,
                            corner_radius=radius, width=size[0], height=size[1])
    return ctk.CTkLabel(parent, image=img, text="", fg_color="transparent")
