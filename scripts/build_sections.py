#!/usr/bin/env python3
"""
build_sections.py - Write one .ics calendar per section, each with its own color.

Mode 1: new plan from a JSON spec (every event has a "section")
    python build_sections.py spec.json [--check]

Mode 2: split an existing .ics using emoji / keyword rules
    python build_sections.py --split plan.ics rules.json

Both modes:
  - check clashes across ALL events (before splitting),
  - print a table section -> color -> events -> hours,
  - write one file per section: <output_dir>/<n>_<id>.ics
  - optional "combined": true -> also a single all-in-one file.

Messages are in Spanish by default; add "lang": "en" to the JSON for English.
The format is documented in references/formato_spec.md (ES) or
references/spec_format.md (EN).
"""
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_ics import (  # noqa: E402
    HEX_RE, ID_RE, esc, fold, horizon_of, load_spec, msgs, norm_emoji,
    occurrences, print_problems, render_calendar, report, unesc, validate,
    write_text)


def table(rows, t):
    h = t["tbl"]
    print(f"\n{h[0]:<3}{h[1]:<34}{h[2]:<22}{h[3]:>8}{h[4]:>8}")
    for r in rows:
        print(f"{r[0]:<3}{r[1]:<34}{r[2]:<22}{r[3]:>8}{r[4]:>8}")


def validate_sections(spec: dict, t: dict):
    """Return (errors, ids) for the "sections" list and "output_dir"."""
    errs, ids = [], []
    if "output_dir" not in spec:
        errs.append(t["missing"].format(f="output_dir"))
    if not spec.get("sections"):
        errs.append(t["missing"].format(f="sections"))
    for i, sec in enumerate(spec.get("sections") or [], 1):
        label = t["sec_label"].format(i=i)
        for f in ("id", "name", "color"):
            if f not in sec:
                errs.append(f"{label}: " + t["missing"].format(f=f))
        sid = sec.get("id")
        if sid is not None:
            if not ID_RE.match(str(sid)):
                errs.append(f"{label}: " + t["bad_id"].format(v=sid))
            if sid in ids:
                errs.append(f"{label}: " + t["dup_id"].format(v=sid))
            ids.append(sid)
        if "color" in sec and not HEX_RE.match(str(sec["color"])):
            errs.append(f"{label}: " + t["bad_color"].format(v=sec["color"]))
    return errs, ids


def color_label(sec):
    return f"{sec.get('color_name', '')} {sec['color']}".strip()


# ------------------------------------------------------------ mode 1: spec
def from_spec(path, check_only=False) -> int:
    spec = load_spec(path)
    t = msgs(spec)
    errs, warns = validate(spec, require_output=False)
    serrs, ids = validate_sections(spec, t)
    errs += serrs
    for i, ev in enumerate(spec.get("events") or [], 1):
        if ev.get("section") not in ids:
            errs.append(t["label"].format(i=i, t=ev.get("title", "?")) + ": "
                        + t["bad_section"].format(v=ev.get("section")))
    if print_problems(errs, warns, t):
        return 1

    report(spec)  # clashes across the whole plan
    horizon = horizon_of(spec)  # None when every event is all-day
    out_dir = spec["output_dir"]
    base = {k: v for k, v in spec.items() if k not in ("sections", "events", "output_dir")}
    rows, written = [], []
    for n, sec in enumerate(spec["sections"], 1):
        evs = [ev for ev in spec["events"] if ev["section"] == sec["id"]]
        if not evs:
            continue
        hours = 0.0
        if horizon is not None:
            for ev in evs:
                for s, e in occurrences(ev, spec["timezone"], horizon):
                    hours += (e - s).total_seconds() / 3600
        rows.append((n, sec["name"], color_label(sec), len(evs), f"{hours:.1f}"))
        if check_only:
            continue
        sub = dict(base, calendar_name=sec["name"], color=sec["color"], events=evs)
        fn = os.path.join(out_dir, f"{n}_{sec['id']}.ics")
        write_text(fn, render_calendar(sub))
        written.append(fn)

    if spec.get("combined") and not check_only:
        sub = dict(base, events=spec["events"])
        sub.setdefault("calendar_name", t["combined_name"])
        fn = os.path.join(out_dir, t["combined_file"])
        write_text(fn, render_calendar(sub))
        written.append(fn)

    table(rows, t)
    for fn in written:
        print("📄", fn)
    return 0


# ----------------------------------------------------- mode 2: split a .ics
def read_unfolded(ics_path: str) -> str:
    """Read an .ics with CRLF or LF line endings and unfold continuation lines.
    Unfolding happens on bytes so a fold inside a UTF-8 character is rejoined."""
    with open(ics_path, "rb") as f:
        raw = f.read()
    raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    raw = re.sub(rb"\n[ \t]", b"", raw)
    return raw.decode("utf-8-sig", errors="replace")


def split_existing(ics_path, rules_path) -> int:
    rules = load_spec(rules_path)
    t = msgs(rules)
    errs, ids = validate_sections(rules, t)
    default = rules.get("default", ids[-1] if ids else None)
    if ids and default not in ids:
        errs.append(t["bad_default"].format(v=default))
    if print_problems(errs, [], t):
        return 1

    try:
        txt = read_unfolded(ics_path)
    except OSError as err:
        print(t["read_err"].format(path=ics_path, err=err))
        return 1
    tz_blocks = re.findall(r"BEGIN:VTIMEZONE\n.*?END:VTIMEZONE", txt, re.S)
    events = re.findall(r"BEGIN:VEVENT\n.*?END:VEVENT", txt, re.S)
    if not events:
        print(t["no_vevents"])
        return 1
    m = re.search(r"^X-WR-TIMEZONE[^:]*:(.*)$", txt, re.M)
    wr_tz = m.group(1).strip() if m else None

    sections = rules["sections"]
    by_id = {s["id"]: s for s in sections}

    def classify(ev):
        m = re.search(r"^SUMMARY[^:]*:(.*)$", ev, re.M)
        title = unesc(m.group(1)) if m else ""
        key, low = norm_emoji(title), title.lower()
        for s in sections:                       # 1st: leading emoji
            if any(key.startswith(norm_emoji(e)) for e in s.get("emojis", [])):
                return s["id"], title, False
        for s in sections:                       # 2nd: keywords
            if any(k.lower() in low for k in s.get("keywords", [])):
                return s["id"], title, False
        return default, title, True

    groups, fallback = defaultdict(list), []
    for ev in events:
        sid, title, fb = classify(ev)
        groups[sid].append(ev)
        if fb:
            fallback.append(title)

    rows = []
    for n, sec in enumerate(sections, 1):
        evs = groups.get(sec["id"], [])
        if not evs:
            continue
        L = ["BEGIN:VCALENDAR", "VERSION:2.0",
             f"PRODID:-//calendar-planner//{rules.get('lang', 'es').upper()}",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{esc(sec['name'])}"]
        if wr_tz:
            L.append(f"X-WR-TIMEZONE:{wr_tz}")
        L.append(f"X-APPLE-CALENDAR-COLOR:{sec['color']}")
        for b in tz_blocks:
            L += b.split("\n")
        for ev in evs:
            # a per-event COLOR from the source would fight the section color
            L += re.sub(r"^COLOR[;:].*\n", "", ev, flags=re.M).split("\n")
        L.append("END:VCALENDAR")
        fn = os.path.join(rules["output_dir"], f"{n}_{sec['id']}.ics")
        write_text(fn, "\r\n".join(fold(x) for x in L) + "\r\n")
        rows.append((n, sec["name"], color_label(sec), len(evs), "-"))
        print("📄", fn)

    table(rows, t)
    print("\n" + t["total"].format(a=sum(r[3] for r in rows), b=len(events)))
    if fallback:
        print("\n" + t["fallback"].format(n=len(fallback), name=by_id[default]["name"]))
        for title in sorted(set(fallback)):
            print("   ·", title)
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if not args:
        print(__doc__)
        return 1
    if args[0] == "--split":
        if len(args) < 3:
            print(msgs({})["split_usage"] + "\n" + msgs({"lang": "en"})["split_usage"])
            return 1
        return split_existing(args[1], args[2])
    return from_spec(args[0], check_only=check)


if __name__ == "__main__":
    sys.exit(main())
