"""Design system for the Inkognito Studios desktop app.

Central place for the colour palette, typography, spacing scale, asset
resolution and image helpers. Every screen imports from here so the whole
application shares one visual language.
"""
import os

from PIL import Image, ImageDraw, ImageTk, ImageFilter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

HERO_IMG = os.path.join(ASSETS_DIR, "hero", "hero.jpg")
AUTH_IMG = os.path.join(ASSETS_DIR, "backgrounds", "background.jpg")
APP_BG_IMG = os.path.join(ASSETS_DIR, "backgrounds", "app_bg.jpg")
BANNER_ARTIST = os.path.join(ASSETS_DIR, "banners", "featured_artist.jpg")
BANNER_PACKAGES = os.path.join(ASSETS_DIR, "banners", "promo_packages.jpg")
GALLERY_DIR = os.path.join(ASSETS_DIR, "gallery")
EMPTY_DIR = os.path.join(ASSETS_DIR, "empty")

PLACEHOLDER = os.path.join(ASSETS_DIR, "package_images", "placeholder.jpg")

# Hero banner gradient (grey) — replaces the photo so the headline pops
HERO_GRAD_FROM = "#16161C"
HERO_GRAD_TO = "#3C3C48"

# ---------------------------------------------------------------------------
# Colour palette — premium dark tattoo-studio aesthetic
# ---------------------------------------------------------------------------
BG            = "#0B0B0D"   # app background
SIDEBAR       = "#0F0F12"   # sidebar / deepest surface
SURFACE       = "#151519"   # large panels
CARD          = "#1A1A1F"   # cards
CARD_HOVER    = "#202027"   # card hover
ELEVATED      = "#232329"   # elevated / inputs
ELEVATED_HI   = "#2B2B33"   # input hover
BORDER        = "#2C2C34"   # hairline border
BORDER_SOFT   = "#232329"   # very soft divider

RED           = "#E11D2E"   # primary accent
RED_HOVER     = "#FF2F45"
RED_PRESSED   = "#A8121F"
RED_SOFT      = "#2A1116"   # translucent red wash
CRIMSON       = "#8E1220"

GOLD          = "#C9A227"   # premium highlight
TEXT          = "#F5F5F7"
TEXT_SEC      = "#A2A2AE"
TEXT_MUTED    = "#6E6E7A"
TEXT_ON_RED   = "#FFFFFF"

SUCCESS       = "#2FBF71"
SUCCESS_SOFT  = "#12291D"
WARNING       = "#E3A008"
WARNING_SOFT  = "#2A2110"
DANGER        = "#E11D2E"
DANGER_SOFT   = "#2A1116"
INFO          = "#4C8DFF"
INFO_SOFT     = "#111C2E"

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FAMILY      = "Segoe UI"
FAMILY_DISP = "Segoe UI Semibold"

F_BRAND   = (FAMILY, 24, "bold")
F_DISPLAY = (FAMILY, 30, "bold")
F_H1      = (FAMILY, 21, "bold")
F_H2      = (FAMILY, 16, "bold")
F_H3      = (FAMILY, 13, "bold")
F_BODY    = (FAMILY, 12)
F_BODY_B  = (FAMILY, 12, "bold")
F_SMALL   = (FAMILY, 11)
F_SMALL_B = (FAMILY, 11, "bold")
F_TINY    = (FAMILY, 10)
F_LABEL   = (FAMILY, 10, "bold")
F_BUTTON  = (FAMILY, 12, "bold")
F_BUTTON_SM = (FAMILY, 11, "bold")
F_MONO    = ("Consolas", 12)
F_MONO_B  = ("Consolas", 13, "bold")
F_NUM     = (FAMILY, 28, "bold")

# ---------------------------------------------------------------------------
# Spacing scale (4px base)
# ---------------------------------------------------------------------------
S1, S2, S3, S4, S5, S6, S7, S8 = 4, 8, 12, 16, 20, 24, 32, 40

RADIUS_SM, RADIUS, RADIUS_LG = 8, 12, 16
RADIUS_PILL = 12


SIDEBAR_W = 232
TOPBAR_H = 68

# ---------------------------------------------------------------------------
# Static gallery content (tattoo styles)
# ---------------------------------------------------------------------------
GALLERY_ITEMS = [
    {"style": "Japanese", "title": "Koi & Waves", "image": "japanese.jpg",
     "desc": "Traditional irezumi with bold outlines, waves and blossoms."},
    {"style": "Blackwork", "title": "Mandala Ink", "image": "blackwork.jpg",
     "desc": "Solid black geometric mandala with fine dotwork shading."},
    {"style": "Realism", "title": "Portrait Study", "image": "realism.jpg",
     "desc": "Hyper realistic black and grey shading in a portrait piece."},
    {"style": "Fine Line", "title": "Botanical Script", "image": "fineline.jpg",
     "desc": "Delicate single-needle linework with a soft, airy feel."},
    {"style": "Geometric", "title": "Sacred Geometry", "image": "geometric.jpg",
     "desc": "Symmetrical patterns built from precise lines and dotwork."},
    {"style": "Traditional", "title": "Sailor Swallow", "image": "traditional.jpg",
     "desc": "Classic American traditional with bold colour and outlines."},
]

GALLERY_STYLES = ["All", "Japanese", "Blackwork", "Realism", "Fine Line",
                  "Geometric", "Traditional"]

# ---------------------------------------------------------------------------
# Asset resolution — works regardless of the current working directory
# ---------------------------------------------------------------------------
_SEARCH_DIRS = [
    ASSETS_DIR,
    os.path.join(ASSETS_DIR, "package_images"),
    os.path.join(ASSETS_DIR, "artist_images"),
    os.path.join(ASSETS_DIR, "gallery"),
    os.path.join(ASSETS_DIR, "hero"),
    os.path.join(ASSETS_DIR, "banners"),
    os.path.join(ASSETS_DIR, "backgrounds"),
    os.path.join(ASSETS_DIR, "empty"),
    os.path.join(ASSETS_DIR, "customer_references"),
]


def resolve_asset(path):
    """Return an existing absolute path for a stored image value, or None."""
    if not path:
        return None
    path = str(path).replace("\\", "/")
    if os.path.isabs(path) and os.path.exists(path):
        return path
    name = os.path.basename(path)
    for folder in (os.path.dirname(path),) + tuple(_SEARCH_DIRS):
        if not folder:
            continue
        candidate = os.path.join(folder, name)
        if os.path.exists(candidate):
            return candidate
    return None


# ---------------------------------------------------------------------------
# Image helpers (cached)
# ---------------------------------------------------------------------------
_image_cache = {}
_raw_cache = {}


def open_source(path):
    """Open and cache a raw PIL RGB image."""
    resolved = resolve_asset(path)
    if not resolved:
        resolved = PLACEHOLDER
    if resolved in _raw_cache:
        return _raw_cache[resolved]
    try:
        img = Image.open(resolved).convert("RGB")
    except Exception:
        try:
            img = Image.open(PLACEHOLDER).convert("RGB")
        except Exception:
            img = Image.new("RGB", (600, 400), (26, 26, 31))
    _raw_cache[resolved] = img
    return img


def cover_crop(img, size):
    """Resize `img` to exactly `size` cropping the overflow (no distortion)."""
    tw, th = max(1, int(size[0])), max(1, int(size[1]))
    stride = max(tw / img.width, th / img.height)
    nw, nh = max(tw, int(img.width * stride + 0.5)), max(th, int(img.height * stride + 0.5))
    resized = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def contain(img, size):
    """Fit `img` inside `size` preserving aspect ratio."""
    copy = img.copy()
    copy.thumbnail((max(1, size[0]), max(1, size[1])), Image.LANCZOS)
    return copy


def rounded(img, radius):
    """Return an RGBA copy of `img` with rounded corners."""
    radius = int(radius)
    if radius <= 0:
        return img.convert("RGBA")
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1],
                                           radius=radius, fill=255)
    img.putalpha(mask)
    return img


def darkened(img, amount=0.35):
    """Darken an image by blending toward black (amount 0..1)."""
    if amount <= 0:
        return img
    overlay = Image.new("RGB", img.size, (0, 0, 0))
    return Image.blend(img.convert("RGB"), overlay, amount)


def hex_to_rgb(value):
    """Convert a ``#rrggbb`` string into an ``(r, g, b)`` tuple."""
    value = str(value).lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def linear_gradient(size, start, end, horizontal=True):
    """Return a PIL RGB image filled with a smooth linear gradient."""
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    a, b = hex_to_rgb(start), hex_to_rgb(end)
    steps = 256
    strip = Image.new("RGB", (steps, 1) if horizontal else (1, steps))
    for i in range(steps):
        t = i / (steps - 1)
        color = tuple(int(s + (e - s) * t) for s, e in zip(a, b))
        strip.putpixel((i, 0) if horizontal else (0, i), color)
    return strip.resize((w, h), Image.BILINEAR)


def gradient_scrim(size, direction="left", strength=0.92, color=(11, 11, 13)):
    """Build a PIL gradient used to keep text readable over photos."""
    w, h = size
    grad = Image.new("L", (w, h), 0)
    px = grad.load()
    for x in range(w):
        if direction == "left":
            f = 1 - (x / max(1, w - 1))
        else:
            f = x / max(1, w - 1)
        value = int(255 * strength * (f ** 1.4))
        for y in range(h):
            px[x, y] = value
    layer = Image.new("RGB", (w, h), color)
    return layer, grad


def photo(path, size, mode="cover", radius=0):
    """Return a cached ``CTkImage`` for the given asset and size."""
    import customtkinter as ctk
    key = (str(path), tuple(size), mode, int(radius))
    cached = _image_cache.get(key)
    if cached is not None:
        return cached
    img = open_source(path)
    img = cover_crop(img, size) if mode == "cover" else contain(img, size)
    if radius:
        img = rounded(img, radius)
    try:
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        ctk_img = None
    _image_cache[key] = ctk_img
    return ctk_img


def tk_photo(img):
    """Return a Tk PhotoImage while keeping a reference alive."""
    photo_img = ImageTk.PhotoImage(img)
    _image_cache[("_tk", id(photo_img))] = photo_img
    return photo_img
