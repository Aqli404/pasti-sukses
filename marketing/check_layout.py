"""Measure rendered text width with the real Segoe UI fonts and report layout issues.

Since the designer/agent cannot view the raster output, this script provides a
quantitative substitute: every <text> element is measured with the actual font
that Inkscape will use, then checked against its container (canvas edge / pill /
card / chip). Exit code != 0 if anything overflows.
"""
import os
import re
import sys
from dataclasses import dataclass

from PIL import ImageFont

FONTS = {
    "400": r"C:\Windows\Fonts\segoeui.ttf",
    "600": r"C:\Windows\Fonts\seguisb.ttf",
    "700": r"C:\Windows\Fonts\segoeuib.ttf",
    "800": r"C:\Windows\Fonts\segoeuib.ttf",
}

# emoji glyphs are not in Segoe UI; render them with the emoji font so the
# measured advance roughly matches what Inkscape draws.
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\u2b00-\u2bff\ufe0f\u2600-\u26ff]"
)
EMOJI_FONT = r"C:\Windows\Fonts\seguiemj.ttf"

_cache: dict = {}


def _font(path: str, size: int):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def text_width(text: str, size: int, weight: str, spacing: float = 0.0) -> float:
    """Approximate advance width of `text` at `size`px, honouring SVG letter-spacing."""
    if not text:
        return 0.0
    base = _font(FONTS.get(str(weight), FONTS["400"]), size)
    emoji = _font(EMOJI_FONT, size)
    total = 0.0
    plain = ""
    for ch in text:
        if EMOJI_RE.match(ch):
            if plain:
                total += base.getlength(plain)
                plain = ""
            total += emoji.getlength(ch) + size * 0.15
        else:
            plain += ch
    if plain:
        total += base.getlength(plain)
    total += spacing * len(text)
    return total


@dataclass
class Text:
    raw: str
    content: str
    x: float
    y: float
    size: float
    weight: str
    anchor: str
    spacing: float

    @property
    def width(self) -> float:
        plain = re.sub(r"<[^>]+>", "", self.content)
        plain = plain.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        return text_width(plain, int(self.size), self.weight, self.spacing)

    @property
    def left(self) -> float:
        if self.anchor == "middle":
            return self.x - self.width / 2
        if self.anchor == "end":
            return self.x - self.width
        return self.x

    @property
    def right(self) -> float:
        return self.left + self.width


def parse_texts(svg: str) -> list[Text]:
    """Parse <text> elements, inheriting font/anchor attributes from ancestor <g>."""
    texts = []
    group_stack: list[dict] = []
    tag_re = re.compile(r"<(/?)(g|text)\b([^>]*?)(/?)>", re.S)
    pos = 0
    for m in tag_re.finditer(svg):
        closing, tag, attrs, selfclose = m.group(1), m.group(2), m.group(3), m.group(4)
        if tag == "g":
            if closing:
                if group_stack:
                    group_stack.pop()
            elif selfclose:
                pass
            else:
                group_stack.append(_attrs(attrs))
        elif tag == "text":
            if closing:
                continue
            inherited = {}
            for g in group_stack:
                inherited.update({k: v for k, v in g.items() if k not in inherited})
            own = _attrs(attrs)
            # find matching </text> and grab inner content
            end = svg.find("</text>", m.end())
            inner = svg[m.end():end] if end != -1 else ""
            x = float(own.get("x", inherited.get("x", "0")))
            tm = re.search(r'<tspan[^>]*\bx="([\d.]+)"', inner)
            if tm and "text-anchor" not in own and "text-anchor" not in inherited:
                x = float(tm.group(1))
            texts.append(
                Text(
                    raw=m.group(0),
                    content=inner,
                    x=x,
                    y=float(own.get("y", inherited.get("y", "0"))),
                    size=float(own.get("font-size", inherited.get("font-size", "16"))),
                    weight=own.get("font-weight", inherited.get("font-weight", "400")),
                    anchor=own.get(
                        "text-anchor", inherited.get("text-anchor", "start")
                    ),
                    spacing=float(
                        own.get("letter-spacing", inherited.get("letter-spacing", "0"))
                    ),
                )
            )
    return texts


def _attrs(s: str) -> dict:
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r'([\w-]+)="([^"]*)"', s)
    }


def check(path: str, width: int = 1080, height: int = 1920) -> list[str]:
    svg = open(path, encoding="utf-8").read()
    problems = []
    for t in parse_texts(svg):
        label = re.sub(r"<[^>]+>", "", t.content).strip()[:40]
        if t.left < 10 or t.right > width - 10:
            problems.append(
                f"  overflow-X [{label}] left={t.left:.0f} right={t.right:.0f} (canvas 0..{width})"
            )
        if t.y > height - 10 or t.y < 10:
            problems.append(f"  overflow-Y [{label}] baseline={t.y:.0f} (canvas 0..{height})")
    return problems


def _find(texts: list[Text], needle: str) -> Text | None:
    for t in texts:
        plain = re.sub(r"<[^>]+>", "", t.content)
        if needle in plain:
            return t
    return None


# TikTok photo posts overlay UI on top of the image, so text must stay inside a
# safe zone: right rail (like/share/comment) covers x>=900, the top bar covers
# y<200, and caption/username/music covers y>1600.
TIKTOK_SAFE = {"x0": 70, "x1": 880, "y0": 230, "y1": 1560}


def check_tiktok_safezone(path: str) -> list[str]:
    problems = []
    for t in parse_texts(open(path, encoding="utf-8").read()):
        label = re.sub(r"<[^>]+>", "", t.content).strip()[:40]
        if t.left < TIKTOK_SAFE["x0"] or t.right > TIKTOK_SAFE["x1"]:
            problems.append(
                f"  [tiktok safe-X] [{label}] L={t.left:.0f} R={t.right:.0f} "
                f"(must be {TIKTOK_SAFE['x0']}..{TIKTOK_SAFE['x1']})"
            )
        if t.y < TIKTOK_SAFE["y0"] or t.y > TIKTOK_SAFE["y1"]:
            problems.append(
                f"  [tiktok safe-Y] [{label}] baseline={t.y:.0f} "
                f"(must be {TIKTOK_SAFE['y0']}..{TIKTOK_SAFE['y1']})"
            )
    return problems


def check_containers(path: str) -> list[str]:
    """Verify specific texts stay inside their pill / chip / card containers
    with a comfortable margin. Coordinates mirror the SVG sources."""
    texts = parse_texts(open(path, encoding="utf-8").read())
    problems = []
    name = os.path.basename(path)

    if name == "poster_a.svg":
        # badge pill: rect x=200 w=680 (200..880)
        t = _find(texts, "GRATIS")
        if t and (t.left < 240 or t.right > 840):
            problems.append(f"  [badge pill] text L={t.left:.0f} R={t.right:.0f} outside pill 200..880 (want 240..840)")
        # feature card: rect x=140 w=800 (140..940); text starts x=210
        for needle in ("Lowongan baru", "Sesuai", "Langsung ke"):
            t = _find(texts, needle)
            if t and t.right > 900:
                problems.append(f"  [feature card] '{needle}' R={t.right:.0f} > 900")
        # CTA button: rect x=190 w=700 y=1520 h=120 -> text must sit inside horizontally
        t = _find(texts, "t.me/Sukses")
        if t and (t.left < 230 or t.right > 850):
            problems.append(f"  [CTA] text L={t.left:.0f} R={t.right:.0f} outside 190..890")

    if name == "poster_b.svg":
        # chat chips: rect x=230 w=620 (230..850)
        for needle in ("Senior Backend", "Lemon.io", "UI/UX", "Startup ID", "Digital Marketing", "E-commerce"):
            t = _find(texts, needle)
            if t and t.right > 820:
                problems.append(f"  [chat chip] '{needle}' R={t.right:.0f} > 820")
        # feature lines must clear the canvas with margin
        for needle in ("GRATIS", "Link langsung lamar"):
            t = _find(texts, needle)
            if t and (t.left < 60 or t.right > 1020):
                problems.append(f"  [feature line] '{needle}' L={t.left:.0f} R={t.right:.0f} needs margin >=60")

    if name == "poster_c.svg":
        # top badge pill: rect x=240 w=600 (240..840)
        t = _find(texts, "PROJECT PERTAMA")
        if t and (t.left < 270 or t.right > 810):
            problems.append(f"  [badge pill] text L={t.left:.0f} R={t.right:.0f} outside 240..840 (want 270..810)")
        # stack chips: each rect w=230
        chips = [("Python 3.11", 150, 380), ("Telegram Bot", 425, 655), ("SQLite", 700, 930),
                 ("6 Scrapers", 285, 515), ("Scheduler", 565, 795)]
        for needle, x0, x1 in chips:
            t = _find(texts, needle)
            if t and (t.left < x0 + 12 or t.right > x1 - 12):
                problems.append(f"  [stack chip] '{needle}' L={t.left:.0f} R={t.right:.0f} outside {x0}..{x1}")
        # stat strip: rect x=150 w=780
        for needle in ("183", "8"):
            t = _find(texts, needle)
            if t and (t.left < 170 or t.right > 910):
                problems.append(f"  [stat strip] '{needle}' outside 150..930")
        # repo url must fit
        t = _find(texts, "github.com/Aqli404")
        if t and (t.left < 40 or t.right > 1040):
            problems.append(f"  [url] L={t.left:.0f} R={t.right:.0f} outside canvas margin")

    if name.startswith("tt_"):
        # badge pill on tt_01: rect x=280 w=520 (280..800)
        t = _find(texts, "BUILD WITH AI")
        if t and (t.left < 305 or t.right > 775):
            problems.append(f"  [tt pill] BUILD WITH AI L={t.left:.0f} R={t.right:.0f} outside 280..800")
        # overview card on tt_01: rect x=195 w=690 (195..885), text starts x=260
        for needle in ("Isi carousel", "Kenapa gue", "Gimana AI", "Kode lengkap"):
            t = _find(texts, needle)
            if t and t.right > 855:
                problems.append(f"  [tt card] '{needle}' R={t.right:.0f} > 855")
        # feature card on tt_02: rect x=150 w=730 (150..880)
        for needle in ("Lowongan baru", "Sesuai", "Langsung ke", "gratis · tanpa"):
            t = _find(texts, needle)
            if t and t.right > 850:
                problems.append(f"  [tt card] '{needle}' R={t.right:.0f} > 850")
        # chips on tt_03: each rect w=210
        for needle, x0, x1 in (
            ("Python 3.11", 200, 410), ("Telegram Bot", 435, 645), ("SQLite", 670, 880),
            ("6 Scrapers", 317, 527), ("Scheduler", 552, 762),
        ):
            t = _find(texts, needle)
            if t and (t.left < x0 + 8 or t.right > x1 - 8):
                problems.append(f"  [tt chip] '{needle}' L={t.left:.0f} R={t.right:.0f} outside {x0}..{x1}")
        # stat strip on tt_03: rect x=200 w=680
        for needle in ("183", "24/7"):
            t = _find(texts, needle)
            if t and (t.left < 210 or t.right > 870):
                problems.append(f"  [tt stat] '{needle}' outside 200..880")
        # QR card on tt_04: rect x=340 w=400 (340..740)
        t = _find(texts, "Scan → buka repository")
        if t and (t.left < 355 or t.right > 725):
            problems.append(f"  [tt QR] label L={t.left:.0f} R={t.right:.0f} outside 340..740")
        # CTA pills on tt_04: rect x=195 w=690 (195..885)
        for needle in ("Star", "FOLLOW @rosif.ai"):
            t = _find(texts, needle)
            if t and (t.left < 220 or t.right > 860):
                problems.append(f"  [tt CTA] '{needle}' L={t.left:.0f} R={t.right:.0f} outside 195..885")

    return problems


def main() -> None:
    import glob

    any_problem = False
    targets = sorted(glob.glob(os.path.join("marketing", "poster_*.svg")))
    targets += sorted(glob.glob(os.path.join("marketing", "tiktok", "tt_*.svg")))
    for path in targets:
        problems = check(path) + check_containers(path)
        if os.path.basename(path).startswith("tt_"):
            problems += check_tiktok_safezone(path)
        status = "OK" if not problems else f"{len(problems)} PROBLEM(S)"
        print(f"{os.path.relpath(path, 'marketing'):24} {status}")
        for p in problems:
            print(p)
            any_problem = True
    print("\nLAYOUT CHECK:", "FAILED" if any_problem else "ALL PASSED")
    sys.exit(1 if any_problem else 0)


if __name__ == "__main__":
    main()
