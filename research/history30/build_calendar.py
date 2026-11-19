"""Build the scheduled-news calendar for the 30-year study (see PREREG.md).

FOMC: parses the Fed's own pages, saved by `download_fed` into a folder:
  fomchistoricalYYYY.htm (one per year, 1996-2020) and fomccalendars.htm (2021 on).
Only scheduled meetings count: conference calls, "(unscheduled)" meetings, notation votes and
"(cancelled)" meetings are dropped, since they weren't known in advance. The decision day is the
meeting's last day.

CPI and jobs: bls.gov blocks scripted downloads here, so `bls_release_dates.txt` holds the dates read
from the BLS archive pages' links (2008-02 on), checked as PREREG.md describes.

Usage:
  python3 -I research/history30/build_calendar.py download <dir>   # fetch the Fed pages
  python3 -I research/history30/build_calendar.py build <dir>      # write events.csv
"""
import csv
import datetime as dt
import html
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}
FIRST_YEAR, LAST_HIST_YEAR = 1996, 2020


def download_fed(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    urls = {f"h{y}.html": f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{y}.htm"
            for y in range(FIRST_YEAR, LAST_HIST_YEAR + 1)}
    urls["current.html"] = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    for name, url in urls.items():
        subprocess.run(["curl", "-sS", "--max-time", "60", "-o", str(folder / name), url], check=True)


def month_number(name):
    name = name.strip().rstrip(".")
    for full, n in MONTHS.items():
        if name == full or (len(name) == 3 and full.startswith(name)):
            return n
    raise KeyError(name)


def last_day(year, month_text, day_text):
    """'January', '27-28' -> Jan 28; 'April/May', '30-1' -> May 1; 'Jan/Feb', '31-1' -> Feb 1;
    'October', '31-1' -> Nov 1 (range runs into a month the page doesn't name)."""
    months = [month_number(m) for m in re.findall(r"[A-Za-z]+", month_text)]
    days = [int(d) for d in re.findall(r"\d+", day_text)]
    month = months[-1]
    if len(days) == 2 and days[1] < days[0] and len(months) == 1:
        month += 1
    if month == 13:
        year, month = year + 1, 1
    return dt.date(year, month, days[-1])


def parse_historical(text, year):
    """<h5 ...>June 27-28 Meeting - 2000</h5> headings on fomchistoricalYYYY.htm. Also handles
    'June 30-July 1 Meeting', 'Jan/Feb 31-1 Meeting'. Keeps scheduled meetings only."""
    out = []
    for raw in re.findall(r"<h5[^>]*>([^<]*)</h5>", text):
        label = " ".join(html.unescape(raw).split())
        m = re.fullmatch(r"(.+) Meeting - (\d{4})", label)
        if not m or int(m.group(2)) != year or "(" in m.group(1):
            continue  # conference calls, (unscheduled), (cancelled), (notation vote)
        when = m.group(1)
        months = " ".join(re.findall(r"[A-Za-z/]+", when))
        out.append(last_day(year, months, " ".join(re.findall(r"\d+", when))))
    return out


def parse_current(text):
    """fomccalendars.htm: per-year panels with month/date cells, e.g. 'January' / '27-28'."""
    out = []
    parts = re.split(r"<h4><a id=\"\d+\">(\d{4}) FOMC Meetings", text)
    for i in range(1, len(parts), 2):
        year, body = int(parts[i]), parts[i + 1]
        months = re.findall(r'fomc-meeting__month[^>]*><strong>([^<]*)</strong>', body)
        days = re.findall(r'fomc-meeting__date[^>]*>([^<]*)<', body)
        if len(months) != len(days):
            raise ValueError(f"{year}: {len(months)} months vs {len(days)} dates")
        for mon, day in zip(months, days):
            day = html.unescape(day).strip()
            if re.search(r"[a-z]", day.replace("*", "")):  # "(notation vote)", "(unscheduled)", ...
                continue
            out.append(last_day(year, mon.strip(), day.replace("*", "")))
    return out


def fomc_dates(folder):
    folder = Path(folder)
    dates = []
    for y in range(FIRST_YEAR, LAST_HIST_YEAR + 1):
        got = parse_historical((folder / f"h{y}.html").read_text(errors="replace"), y)
        if not 7 <= len(got) <= 9:
            raise ValueError(f"{y}: {len(got)} scheduled meetings")
        dates += got
    cur = [d for d in parse_current((folder / "current.html").read_text(errors="replace"))
           if d.year > LAST_HIST_YEAR]
    dates = sorted(set(dates + cur))
    # A "Meeting" one or two days before another one is the same meeting split in two on the page
    # (2003-09-15 has only an agenda; the decision came on 2003-09-16). Keep the later day.
    return [d for i, d in enumerate(dates)
            if not (i + 1 < len(dates) and (dates[i + 1] - d).days <= 2)]


def bls_dates():
    out = []
    for line in (HERE / "bls_release_dates.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        event, *days = line.split()
        out += [(event, dt.date.fromisoformat(d)) for d in days]
    return out


def build(folder):
    rows = [("fomc", d) for d in fomc_dates(folder)] + bls_dates()
    for _, d in rows:
        if d.weekday() > 4:
            raise ValueError(f"weekend date {d}")
    rows.sort(key=lambda r: (r[1], r[0]))
    with open(HERE / "events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "event"])
        for event, d in rows:
            w.writerow([d.isoformat(), event])
    counts = {}
    for event, _ in rows:
        counts[event] = counts.get(event, 0) + 1
    print("wrote", HERE / "events.csv", counts)


if __name__ == "__main__":
    cmd, folder = sys.argv[1], sys.argv[2]
    {"download": download_fed, "build": build}[cmd](folder)
