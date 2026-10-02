"""Text normalization + Persian/Gregorian date helpers."""
import re

_DIG = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_CH = str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "ئ": "ی", "أ": "ا", "إ": "ا", "ؤ": "و",
                     "\u200c": " ", "\u200f": "", "\u200e": "", "\u064b": "", "\u064c": "", "\u064d": "",
                     "\u064e": "", "\u064f": "", "\u0650": "", "\u0651": "", "\u0652": ""})

def digits(s):
    """Persian/Arabic-Indic digits -> ASCII."""
    return (s or "").translate(_DIG)

def norm(s):
    """Search normalisation: ASCII digits, unified Persian letters, no ZWNJ/diacritics, lowercase, single spaces."""
    s = digits(s).translate(_CH).lower()
    return re.sub(r"\s+", " ", s).strip()

def clean(s, n=200):
    """Store-friendly text: unified ی/ک, trimmed, collapsed blanks (digits untouched)."""
    s = (s or "").replace("ي", "ی").replace("ك", "ک")
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s[:n]

def to_fa_digits(s):
    return str(s).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

# ---- Jalali <-> Gregorian (standard algorithm) ----
def jalali_to_gregorian(jy, jm, jd):
    jy -= 979; jm -= 1; jd -= 1
    j_days = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    g_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_no = 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4
    for i in range(jm): j_no += j_days[i]
    j_no += jd
    g_no = j_no + 79
    gy = 1600 + 400 * (g_no // 146097); g_no %= 146097
    leap = True
    if g_no >= 36525:
        g_no -= 1
        gy += 100 * (g_no // 36524); g_no %= 36524
        if g_no >= 365: g_no += 1
        else: leap = False
    gy += 4 * (g_no // 1461); g_no %= 1461
    if g_no >= 366:
        leap = False; g_no -= 1
        gy += g_no // 365; g_no %= 365
    i = 0
    while g_no >= g_days[i] + (1 if i == 1 and leap else 0):
        g_no -= g_days[i] + (1 if i == 1 and leap else 0); i += 1
    return gy, i + 1, g_no + 1

def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + g_d_m[gm - 1]
    jy = -1595 + 33 * (days // 12053); days %= 12053
    jy += 4 * (days // 1461); days %= 1461
    if days > 365:
        jy += (days - 1) // 365; days = (days - 1) % 365
    if days < 186: jm = 1 + days // 31; jd = 1 + days % 31
    else: jm = 7 + (days - 186) // 30; jd = 1 + (days - 186) % 30
    return jy, jm, jd

def iso_to_jalali_str(iso):
    """'2026-09-30...' -> '1405/07/08' (or '' on bad input)."""
    try:
        y, m, d = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
        return "%04d/%02d/%02d" % gregorian_to_jalali(y, m, d)
    except Exception:
        return ""

def parse_date(s):
    """'1405/07/15', '2026-10-07', '۱۴۰۵-۷-۱۵' -> ISO 'YYYY-MM-DD' or None (Jalali if year < 1700)."""
    m = re.fullmatch(r"\s*(\d{4})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*", digits(s))
    if not m: return None
    y, mo, d = map(int, m.groups())
    if not (1 <= mo <= 12 and 1 <= d <= 31): return None
    if y < 1700:
        if y < 1300: return None
        y, mo, d = jalali_to_gregorian(y, mo, d)
    try:
        import datetime; datetime.date(y, mo, d)
    except ValueError:
        return None
    return "%04d-%02d-%02d" % (y, mo, d)

def birth_to_gregorian(y, this_year):
    """Accepts a Jalali (1300-1500) or Gregorian (1900-this_year) year. Returns Gregorian year or None."""
    if 1300 <= y <= 1500: y += 621
    if 1900 <= y <= this_year: return y
    return None
