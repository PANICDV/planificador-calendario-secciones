#!/usr/bin/env python3
"""
build_ics.py - Turn a JSON spec into an importable .ics calendar
(Google Calendar, Apple Calendar, Outlook).

Usage:
    python build_ics.py spec.json            # validate and write the .ics
    python build_ics.py spec.json --check    # validate only, write nothing

Besides writing the file it:
  - validates the spec and reports every problem at once,
  - builds a VTIMEZONE with the zone's real DST rules (RRULE-based, so
    open-ended recurring events stay correct in future years),
  - detects clashes between timed events (expanding recurring ones),
  - prints total hours per category (first emoji/word of each title).

Messages are in Spanish by default; add "lang": "en" to the spec for English.
Requires Python 3.9+. Recommended: python-dateutil (clash check for recurring
events) and, on Windows, tzdata. See requirements.txt.
The spec format is documented in references/formato_spec.md (ES) or
references/spec_format.md (EN).
"""
import hashlib
import json
import os
import re
import sys
from calendar import monthrange
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone

if sys.version_info < (3, 9):
    sys.exit("Python 3.9+ is required (zoneinfo) / Se requiere Python 3.9 o superior.")

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # noqa: E402

try:
    from dateutil.rrule import rrulestr
except ImportError:  # recurring events are then not expanded for the clash check
    rrulestr = None

# Windows consoles default to a legacy code page and crash on emojis.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ------------------------------------------------------------------ messages
MSG = {
    "es": {
        "no_clash": "✅ Sin choques entre eventos con hora.",
        "clashes": "⚠️  {n} choque(s) detectado(s):",
        "more": "   … y {n} más",
        "hours": "Horas por categoría (incluye repeticiones):",
        "written": "📄 {path}  ({n} eventos)",
        "no_dateutil": ("⚠️  Falta python-dateutil: los eventos repetitivos no se expandieron, "
                        "así que sus choques y horas NO se validaron. "
                        "Instálalo con: pip install python-dateutil"),
        "invalid": "❌ La especificación tiene {n} problema(s):",
        "warn": "⚠️  {msg}",
        "read_err": "❌ No se pudo leer {path}: {err}",
        "missing": "falta el campo '{f}'",
        "no_events": "la lista 'events' está vacía",
        "bad_lang": "'lang' debe ser 'es' o 'en'",
        "tz_unknown": ("zona horaria desconocida: '{tz}'. Usa un nombre IANA "
                       "(America/Lima, Europe/Madrid…). En Windows instala antes: pip install tzdata"),
        "no_title": "falta 'title'",
        "ev_need": "necesita 'start' y 'end' (evento con hora) o 'date' (todo el día)",
        "bad_dt": "'{f}' no es una fecha-hora válida (AAAA-MM-DDTHH:MM): {v}",
        "aware_dt": "'{f}' debe ser hora local, sin Z ni ±hh:mm (la zona la da 'timezone'): {v}",
        "bad_date": "'{f}' no es una fecha válida (AAAA-MM-DD): {v}",
        "end_before": "'end' debe ser posterior a 'start'",
        "end_date_before": "'end_date' es anterior a 'date'",
        "bad_freq": "repeat.freq debe ser DAILY, WEEKLY, MONTHLY o YEARLY",
        "bad_byday": "repeat.byday tiene códigos inválidos: {v} (usa MO, TU, WE, TH, FR, SA, SU)",
        "until_count": "repeat no puede llevar 'until' y 'count' a la vez",
        "bad_until": "repeat.until no es una fecha válida: {v}",
        "bad_color": "el color debe ser hex #RRGGBB: {v}",
        "bad_alarm": "'alarm_min' debe ser un número de minutos ≥ 0",
        "dup": "{label} repite título e inicio del evento {j}; se le asignó un UID distinto",
        "label": "evento {i} «{t}»",
        # sections (build_sections.py)
        "sec_label": "sección {i}",
        "bad_id": "'id' debe ir en minúsculas, sin espacios ni tildes (a-z, 0-9, _ o -): {v}",
        "dup_id": "'id' repetido: {v}",
        "bad_section": "'section' no coincide con ninguna sección: {v}",
        "bad_default": "'default' no coincide con ninguna sección: {v}",
        "no_vevents": "❌ No se encontraron eventos en el archivo.",
        "split_usage": "Uso: build_sections.py --split plan.ics reglas.json",
        "tbl": ("#", "Sección", "Color", "Eventos", "Horas"),
        "total": "Total: {a} de {b} eventos.",
        "fallback": "ℹ️  {n} evento(s) sin regla → '{name}'. Revisa que estén bien ahí:",
        "combined_file": "todo_en_uno.ics",
        "combined_name": "Plan completo",
        "weekdays": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"],
    },
    "en": {
        "no_clash": "✅ No clashes between timed events.",
        "clashes": "⚠️  {n} clash(es) found:",
        "more": "   … and {n} more",
        "hours": "Hours per category (repetitions included):",
        "written": "📄 {path}  ({n} events)",
        "no_dateutil": ("⚠️  python-dateutil is missing: recurring events were not expanded, "
                        "so their clashes and hours were NOT checked. "
                        "Install it with: pip install python-dateutil"),
        "invalid": "❌ The spec has {n} problem(s):",
        "warn": "⚠️  {msg}",
        "read_err": "❌ Could not read {path}: {err}",
        "missing": "missing field '{f}'",
        "no_events": "the 'events' list is empty",
        "bad_lang": "'lang' must be 'es' or 'en'",
        "tz_unknown": ("unknown time zone: '{tz}'. Use an IANA name "
                       "(America/New_York, Europe/London…). On Windows run first: pip install tzdata"),
        "no_title": "missing 'title'",
        "ev_need": "needs 'start' and 'end' (timed event) or 'date' (all-day event)",
        "bad_dt": "'{f}' is not a valid date-time (YYYY-MM-DDTHH:MM): {v}",
        "aware_dt": "'{f}' must be local time, without Z or ±hh:mm ('timezone' sets the zone): {v}",
        "bad_date": "'{f}' is not a valid date (YYYY-MM-DD): {v}",
        "end_before": "'end' must be after 'start'",
        "end_date_before": "'end_date' is before 'date'",
        "bad_freq": "repeat.freq must be DAILY, WEEKLY, MONTHLY or YEARLY",
        "bad_byday": "repeat.byday has invalid codes: {v} (use MO, TU, WE, TH, FR, SA, SU)",
        "until_count": "repeat cannot have both 'until' and 'count'",
        "bad_until": "repeat.until is not a valid date: {v}",
        "bad_color": "color must be hex #RRGGBB: {v}",
        "bad_alarm": "'alarm_min' must be a number of minutes ≥ 0",
        "dup": "{label} repeats the title and start of event {j}; it was given a different UID",
        "label": "event {i} «{t}»",
        "sec_label": "section {i}",
        "bad_id": "'id' must be lowercase, no spaces or accents (a-z, 0-9, _ or -): {v}",
        "dup_id": "duplicate 'id': {v}",
        "bad_section": "'section' does not match any section: {v}",
        "bad_default": "'default' does not match any section: {v}",
        "no_vevents": "❌ No events found in the file.",
        "split_usage": "Usage: build_sections.py --split plan.ics rules.json",
        "tbl": ("#", "Section", "Color", "Events", "Hours"),
        "total": "Total: {a} of {b} events.",
        "fallback": "ℹ️  {n} event(s) matched no rule → '{name}'. Check they belong there:",
        "combined_file": "all_in_one.ics",
        "combined_name": "Full plan",
        "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    },
}


def msgs(spec: dict) -> dict:
    return MSG.get(spec.get("lang", "es"), MSG["es"])


# ----------------------------------------------------------------- utilities
WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
FREQS = {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
ID_RE = re.compile(r"^[a-z0-9_-]+$")
BYDAY_RE = re.compile(r"^[+-]?\d{0,2}(MO|TU|WE|TH|FR|SA|SU)$")
UNTIL_RE = re.compile(r"UNTIL=([0-9TZ]+)", re.I)


def esc(s: str) -> str:
    """Escape TEXT values (RFC 5545 §3.3.11)."""
    return (s.replace("\\", "\\\\").replace(";", "\\;")
             .replace(",", "\\,").replace("\n", "\\n"))


def unesc(s: str) -> str:
    return re.sub(r"\\([\\;,nN])",
                  lambda m: "\n" if m.group(1) in "nN" else m.group(1), s)


def norm_emoji(s: str) -> str:
    """Drop the emoji variation selector so 🖥 and 🖥️ compare equal."""
    return s.replace("\ufe0f", "")


def fold(line: str) -> str:
    """Fold lines at 75 octets without splitting UTF-8 characters (RFC 5545)."""
    out, cur = [], b""
    for ch in line:
        c = ch.encode("utf-8")
        lim = 75 if not out else 74
        if len(cur) + len(c) > lim:
            out.append(cur)
            cur = b""
        cur += c
    out.append(cur)
    return "\r\n ".join(x.decode("utf-8") for x in out)


def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def fmt_local(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def offset_str(td: timedelta) -> str:
    total = int(td.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"{sign}{total // 3600:02d}{(total % 3600) // 60:02d}"


def is_all_day(ev: dict) -> bool:
    return bool(ev.get("all_day")) or "date" in ev


def to_utc_stamp(local: datetime, tzname: str) -> str:
    return (local.replace(tzinfo=ZoneInfo(tzname)).astimezone(timezone.utc)
            .strftime("%Y%m%dT%H%M%SZ"))


def load_spec(path: str) -> dict:
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as err:
        sys.exit(MSG["es"]["read_err"].format(path=path, err=err) + "\n"
                 + MSG["en"]["read_err"].format(path=path, err=err))


# ---------------------------------------------------------------- validation
def _check_dt(v, field, t, problems):
    try:
        d = datetime.fromisoformat(v) if isinstance(v, str) else None
    except ValueError:
        d = None
    if d is None:
        problems.append(t["bad_dt"].format(f=field, v=v))
    elif d.tzinfo is not None:
        problems.append(t["aware_dt"].format(f=field, v=v))
        d = None
    return d


def _check_date(v, field, t, problems):
    try:
        return date.fromisoformat(v) if isinstance(v, str) else None
    except ValueError:
        pass
    problems.append(t["bad_date"].format(f=field, v=v))
    return None


def validate_event(ev: dict, t: dict) -> list:
    p = []
    if not ev.get("title"):
        p.append(t["no_title"])
    if is_all_day(ev):
        if "date" not in ev:
            p.append(t["ev_need"])
        else:
            d = _check_date(ev["date"], "date", t, p)
            if ev.get("end_date"):
                d2 = _check_date(ev["end_date"], "end_date", t, p)
                if d and d2 and d2 < d:
                    p.append(t["end_date_before"])
    elif "start" not in ev or "end" not in ev:
        p.append(t["ev_need"])
    else:
        s = _check_dt(ev["start"], "start", t, p)
        e = _check_dt(ev["end"], "end", t, p)
        if s and e and e <= s:
            p.append(t["end_before"])
    rep = ev.get("repeat")
    if rep and "rrule" not in rep:
        if str(rep.get("freq", "")).upper() not in FREQS:
            p.append(t["bad_freq"])
        byday = rep.get("byday") or []
        if isinstance(byday, str):
            byday = [byday]
        bad = [b for b in byday if not BYDAY_RE.match(str(b).upper())]
        if bad:
            p.append(t["bad_byday"].format(v=bad))
        if rep.get("until") and rep.get("count"):
            p.append(t["until_count"])
        u = rep.get("until")
        if u:
            try:
                (date.fromisoformat if len(str(u)) == 10 else datetime.fromisoformat)(u)
            except (ValueError, TypeError):
                p.append(t["bad_until"].format(v=u))
    if "alarm_min" in ev:
        a = ev["alarm_min"]
        if isinstance(a, bool) or not isinstance(a, (int, float)) or a < 0:
            p.append(t["bad_alarm"])
    return p


def validate(spec: dict, require_output: bool = True):
    """Return (errors, warnings), all already translated."""
    t = msgs(spec)
    errs, warns = [], []
    if spec.get("lang", "es") not in MSG:
        errs.append(t["bad_lang"])
    required = ["timezone", "events"] + (["output"] if require_output else [])
    errs += [t["missing"].format(f=f) for f in required if f not in spec]
    tz = spec.get("timezone")
    if tz:
        try:
            ZoneInfo(tz)
        except (ZoneInfoNotFoundError, ValueError):
            errs.append(t["tz_unknown"].format(tz=tz))
    if spec.get("color") and not HEX_RE.match(str(spec["color"])):
        errs.append(t["bad_color"].format(v=spec["color"]))
    events = spec.get("events")
    if "events" in spec and not events:
        errs.append(t["no_events"])
    seen = {}
    for i, ev in enumerate(events or [], 1):
        label = t["label"].format(i=i, t=ev.get("title", "?"))
        errs += [f"{label}: {p}" for p in validate_event(ev, t)]
        key = (ev.get("title"), ev.get("start") or ev.get("date"))
        if key in seen and not ev.get("uid"):
            warns.append(t["dup"].format(label=label, j=seen[key]))
        seen.setdefault(key, i)
    return errs, warns


def print_problems(errs, warns, t) -> bool:
    for w in warns:
        print(t["warn"].format(msg=w))
    if errs:
        print(t["invalid"].format(n=len(errs)))
        for e in errs:
            print("   ·", e)
    return bool(errs)


# ------------------------------------------------------------- time zone
def _scan_transitions(tz, lo, hi):
    """Every UTC-offset change in [lo, hi) (aware UTC datetimes) as
    (local wall time before the change, offset_from, offset_to, new tzname).
    Searching in UTC avoids ambiguous or non-existent local times."""
    def off(x):
        return x.astimezone(tz).utcoffset()

    out = []
    t = lo
    prev = off(t)
    while t < hi:
        nt = t + timedelta(days=1)
        if off(nt) != prev:
            a, b = t, nt
            while (b - a) > timedelta(seconds=30):
                m = a + (b - a) / 2
                if off(m) == prev:
                    a = m
                else:
                    b = m
            instant = b.replace(second=0, microsecond=0)
            if off(instant) == prev:
                instant += timedelta(minutes=1)
            new = off(instant)
            local_before = (instant + prev).replace(tzinfo=None)
            out.append((local_before, prev, new, instant.astimezone(tz).tzname()))
            prev = new
        t = nt
    return out


def _nth_weekday(year, month, wd, n):
    """Date of the n-th weekday `wd` (0=Monday) of a month; n=-1 is the last one."""
    if n > 0:
        first = date(year, month, 1)
        d = first + timedelta(days=(wd - first.weekday()) % 7 + 7 * (n - 1))
        return d if d.month == month else None
    last = date(year, month, monthrange(year, month)[1])
    return last - timedelta(days=(last.weekday() - wd) % 7)


def _yearly_rule(tr, later, end_year):
    """Express transition `tr` as FREQ=YEARLY;BYMONTH;BYDAY if that rule reproduces
    exactly every later transition of the same kind up to `end_year`."""
    when = tr[0]
    expected = {x[0] for x in later if (x[1], x[2]) == (tr[1], tr[2])}
    cands = []
    nth = (when.day - 1) // 7 + 1
    if nth <= 4:
        cands.append(nth)
    if when.day + 7 > monthrange(when.year, when.month)[1]:
        cands.append(-1)
    for n in cands:
        gen = set()
        for y in range(when.year + 1, end_year):
            d = _nth_weekday(y, when.month, when.weekday(), n)
            if d:
                gen.add(datetime.combine(d, when.time()))
        if gen == expected:
            return f"RRULE:FREQ=YEARLY;BYMONTH={when.month};BYDAY={n}{WEEKDAYS[when.weekday()]}"
    return None


def build_vtimezone(tzname: str, start: datetime, end: datetime) -> list:
    """VTIMEZONE with the real transitions from a year before the plan to a year
    after it. When the zone follows a stable yearly DST pattern, the last two
    transitions carry an RRULE so open-ended events stay right in any later year;
    otherwise the transitions are listed explicitly for ten more years."""
    tz = ZoneInfo(tzname)
    lo = (start - timedelta(days=366)).replace(tzinfo=timezone.utc)
    hi = (end + timedelta(days=366)).replace(tzinfo=timezone.utc)
    end_year = hi.year + 11
    allt = _scan_transitions(tz, lo, datetime(end_year, 1, 1, tzinfo=timezone.utc))
    hi_local = hi.replace(tzinfo=None)
    near = [x for x in allt if x[0] <= hi_local]
    rules = {}
    if len(allt) > len(near):                 # the zone keeps changing after the plan
        emit = allt                           # fallback: explicit list, 10 more years
        if len(near) >= 2:
            a, b = near[-2], near[-1]
            if (a[1], a[2]) == (b[2], b[1]):
                ra = _yearly_rule(a, allt[len(near) - 1:], end_year)
                rb = _yearly_rule(b, allt[len(near):], end_year)
                if ra and rb:
                    rules = {len(near) - 2: ra, len(near) - 1: rb}
                    emit = near
    else:
        emit = near

    def name_at(x):
        return x.astimezone(tz).tzname()

    lines = ["BEGIN:VTIMEZONE", f"TZID:{tzname}"]
    if not emit:
        o = lo.astimezone(tz).utcoffset()
        lines += ["BEGIN:STANDARD", "DTSTART:19700101T000000",
                  f"TZOFFSETFROM:{offset_str(o)}", f"TZOFFSETTO:{offset_str(o)}",
                  f"TZNAME:{name_at(hi)}", "END:STANDARD"]
    else:
        first_from = emit[0][1]
        lines += ["BEGIN:STANDARD", "DTSTART:19700101T000000",
                  f"TZOFFSETFROM:{offset_str(first_from)}",
                  f"TZOFFSETTO:{offset_str(first_from)}",
                  f"TZNAME:{name_at(lo)}", "END:STANDARD"]
        for i, (when, o_from, o_to, name) in enumerate(emit):
            kind = "DAYLIGHT" if o_to > o_from else "STANDARD"
            lines += [f"BEGIN:{kind}", f"DTSTART:{fmt_local(when)}",
                      f"TZOFFSETFROM:{offset_str(o_from)}",
                      f"TZOFFSETTO:{offset_str(o_to)}", f"TZNAME:{name}"]
            if i in rules:
                lines.append(rules[i])
            lines.append(f"END:{kind}")
    lines.append("END:VTIMEZONE")
    return lines


# ---------------------------------------------------------------- recurrence
def build_rrule(rep: dict, tzname: str, all_day: bool = False) -> str:
    """Accept a raw {"rrule": "..."} or friendly fields. UNTIL is written the way
    RFC 5545 requires: a DATE for all-day events, a UTC DATE-TIME otherwise."""
    if "rrule" in rep:
        r = rep["rrule"]
        r = r[6:] if r.upper().startswith("RRULE:") else r

        def fix(m):
            v = m.group(1).upper()
            if all_day:
                return "UNTIL=" + v[:8]
            if len(v) == 8:          # date-only on a timed event → end of that local day
                d = datetime.strptime(v, "%Y%m%d") + timedelta(days=1, seconds=-1)
                return "UNTIL=" + to_utc_stamp(d, tzname)
            if not v.endswith("Z"):  # floating local time → UTC
                return "UNTIL=" + to_utc_stamp(datetime.strptime(v, "%Y%m%dT%H%M%S"), tzname)
            return "UNTIL=" + v
        return "RRULE:" + UNTIL_RE.sub(fix, r)

    parts = [f"FREQ={rep['freq'].upper()}"]
    if rep.get("interval", 1) != 1:
        parts.append(f"INTERVAL={rep['interval']}")
    if rep.get("byday"):
        byday = rep["byday"] if isinstance(rep["byday"], list) else [rep["byday"]]
        parts.append("BYDAY=" + ",".join(str(b).upper() for b in byday))
    if rep.get("bymonthday") is not None:
        parts.append(f"BYMONTHDAY={rep['bymonthday']}")
    if rep.get("bymonth") is not None:
        parts.append(f"BYMONTH={rep['bymonth']}")
    if rep.get("count"):
        parts.append(f"COUNT={rep['count']}")
    elif rep.get("until"):
        u = str(rep["until"])  # local date, inclusive
        if all_day:
            parts.append("UNTIL=" + date.fromisoformat(u[:10]).strftime("%Y%m%d"))
        else:
            dt = datetime.fromisoformat(u)
            if len(u) == 10:
                dt += timedelta(days=1, seconds=-1)
            parts.append("UNTIL=" + to_utc_stamp(dt, tzname))
    return "RRULE:" + ";".join(parts)


# -------------------------------------------------------------------- events
def stable_uid(cal: str, ev: dict, n: int = 0) -> str:
    key = f"{cal}|{ev.get('title')}|{ev.get('start') or ev.get('date')}"
    suffix = f"-{n}" if n else ""
    return hashlib.sha1(key.encode()).hexdigest()[:20] + suffix + "@calendar-planner"


def vevent(ev: dict, tzname: str, uid: str, stamp: str) -> list:
    v = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}"]
    all_day = is_all_day(ev)
    if all_day:
        d = date.fromisoformat(ev["date"])
        d_end = (date.fromisoformat(ev["end_date"]) if ev.get("end_date") else d) \
            + timedelta(days=1)
        v += [f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}",
              f"DTEND;VALUE=DATE:{d_end.strftime('%Y%m%d')}",
              "TRANSP:TRANSPARENT"]
    else:
        s, e = parse_dt(ev["start"]), parse_dt(ev["end"])
        v += [f"DTSTART;TZID={tzname}:{fmt_local(s)}",
              f"DTEND;TZID={tzname}:{fmt_local(e)}"]
    v.append(f"SUMMARY:{esc(ev['title'])}")
    if ev.get("description"):
        v.append(f"DESCRIPTION:{esc(ev['description'])}")
    if ev.get("location"):
        v.append(f"LOCATION:{esc(ev['location'])}")
    if ev.get("repeat"):
        v.append(build_rrule(ev["repeat"], tzname, all_day))
    alarm = ev.get("alarm_min")
    if alarm is not None:
        v += ["BEGIN:VALARM", "ACTION:DISPLAY",
              f"DESCRIPTION:{esc(ev['title'])}",
              f"TRIGGER:-PT{int(alarm)}M", "END:VALARM"]
    v.append("END:VEVENT")
    return v


# ---------------------------------------------------------------- analysis
def horizon_of(spec: dict):
    """Last local moment checked for recurring events, or None if nothing is timed."""
    ends = [parse_dt(ev["end"]) for ev in spec["events"] if not is_all_day(ev)]
    if not ends:
        return None
    h = max(ends)
    if spec.get("range_end"):
        h = max(h, datetime.fromisoformat(spec["range_end"][:10]) + timedelta(days=1))
    return h


def occurrences(ev: dict, tzname: str, horizon: datetime):
    """(start, end) local wall-clock times of each occurrence up to the horizon."""
    if is_all_day(ev):
        return []
    s, e = parse_dt(ev["start"]), parse_dt(ev["end"])
    if not ev.get("repeat") or rrulestr is None:
        return [(s, e)]
    dur = e - s
    rule = build_rrule(ev["repeat"], tzname)[len("RRULE:"):]
    out = []
    for occ in rrulestr(rule, dtstart=s.replace(tzinfo=ZoneInfo(tzname))):
        occ = occ.replace(tzinfo=None)
        if occ > horizon:
            break
        out.append((occ, occ + dur))
        if len(out) >= 5000:
            break
    return out


def category(title: str) -> str:
    return norm_emoji(title.split(" ", 1)[0]) if title else "?"


def analyze(spec: dict):
    """Return (clashes, hours per category, recurring_skipped)."""
    tzname = spec["timezone"]
    horizon = horizon_of(spec)
    if horizon is None:
        return [], {}, False
    skipped = rrulestr is None and any(
        ev.get("repeat") and not is_all_day(ev) for ev in spec["events"])
    occ = []
    for ev in spec["events"]:
        for s, e in occurrences(ev, tzname, horizon):
            occ.append((s, e, ev["title"], bool(ev.get("allow_overlap"))))
    occ.sort()
    clashes = []
    for i in range(len(occ)):
        for j in range(i + 1, len(occ)):
            if occ[j][0] >= occ[i][1]:
                break
            if occ[i][3] or occ[j][3]:
                continue
            clashes.append((occ[i], occ[j]))
    hours = defaultdict(float)
    for s, e, title, _ in occ:
        hours[category(title)] += (e - s).total_seconds() / 3600
    return clashes, dict(hours), skipped


def report(spec: dict):
    """Print clashes (and the dateutil warning); return (clashes, hours)."""
    t = msgs(spec)
    clashes, hours, skipped = analyze(spec)
    if skipped:
        print(t["no_dateutil"])
    wd = t["weekdays"]
    if clashes:
        print(t["clashes"].format(n=len(clashes)))
        for x, y in clashes[:30]:
            print(f"   {wd[x[0].weekday()]} {x[0]:%d/%m %H:%M}-{x[1]:%H:%M} {x[2]}  ×  "
                  f"{y[0]:%H:%M}-{y[1]:%H:%M} {y[2]}")
        if len(clashes) > 30:
            print(t["more"].format(n=len(clashes) - 30))
    else:
        print(t["no_clash"])
    return clashes, hours


def print_hours(hours: dict, t: dict):
    if hours:
        print(t["hours"])
        for k, h in sorted(hours.items(), key=lambda x: -x[1]):
            print(f"   {k:<4} {h:6.1f} h")


# ------------------------------------------------------------------- render
def render_calendar(spec: dict) -> str:
    """Return the full .ics text for a (valid) spec."""
    tzname = spec["timezone"]
    cal = spec.get("calendar_name", "Plan")
    stamps = [parse_dt(ev["start"]) if not is_all_day(ev)
              else datetime.fromisoformat(ev["date"]) for ev in spec["events"]]
    lo, hi = min(stamps), max(stamps)
    if spec.get("range_end"):
        hi = max(hi, datetime.fromisoformat(spec["range_end"][:10]))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lang = spec.get("lang", "es").upper()
    L = ["BEGIN:VCALENDAR", "VERSION:2.0",
         f"PRODID:-//calendar-planner//{lang}",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         f"X-WR-CALNAME:{esc(cal)}", f"X-WR-TIMEZONE:{tzname}"]
    if spec.get("color"):
        L.append(f"X-APPLE-CALENDAR-COLOR:{spec['color']}")
    L += build_vtimezone(tzname, lo, hi)
    used = defaultdict(int)
    for ev in spec["events"]:
        if ev.get("uid"):
            uid = ev["uid"]
        else:
            base = stable_uid(cal, ev)
            uid = stable_uid(cal, ev, used[base])
            used[base] += 1
        L += vevent(ev, tzname, uid, stamp)
    L.append("END:VCALENDAR")
    return "\r\n".join(fold(x) for x in L) + "\r\n"


def write_text(path: str, text: str):
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


# --------------------------------------------------------------------- main
def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__)
        return 1
    spec = load_spec(files[0])
    t = msgs(spec)
    if print_problems(*validate(spec), t):
        return 1
    _, hours = report(spec)
    print_hours(hours, t)
    if "--check" in argv:
        return 0
    write_text(spec["output"], render_calendar(spec))
    print(t["written"].format(path=spec["output"], n=len(spec["events"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
