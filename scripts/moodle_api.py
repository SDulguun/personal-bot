#!/usr/bin/env python3
"""
Moodle scraper for AUM (online.aum.edu.mn) using browser session cookie.

AUM uses Google OAuth so REST API token auth is unavailable to students.
This uses the internal AJAX API with a session cookie instead.

Setup:
1. Log into online.aum.edu.mn in your browser
2. Press Cmd+Option+I → Application tab → Cookies → online.aum.edu.mn
3. Copy the value of the 'MoodleSession' cookie
4. Save it: echo "YOUR_VALUE" > ~/personal-bot/data/moodle-session.txt

Usage: python3 moodle_api.py <deadlines|courses|announcements>
"""
import sys
import json
import re
import urllib.request
from pathlib import Path
from datetime import datetime

BASE = "https://online.aum.edu.mn"
SESSION_FILE = Path.home() / "personal-bot" / "data" / "moodle-session.txt"


def get_session():
    if not SESSION_FILE.exists():
        print("ERROR: No session cookie. Tell the user to run 'setup moodle'.")
        sys.exit(1)
    value = SESSION_FILE.read_text().strip()
    if not value:
        print("ERROR: Session cookie file is empty. Run 'setup moodle'.")
        sys.exit(1)
    return value


def fetch(url, post_data=None):
    session = get_session()
    headers = {
        "Cookie": f"MoodleSession={session}",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    req = urllib.request.Request(url, data=post_data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("ERROR: Session expired. Run 'setup moodle' to refresh.")
        else:
            print(f"ERROR: HTTP {e.code} from Moodle.")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Could not reach Moodle. Check your internet. ({e.reason})")
        sys.exit(1)


def get_sesskey():
    html = fetch(BASE + "/my/")
    if "Log in" in html[:3000]:
        print("ERROR: Session expired. Run 'setup moodle' to refresh.")
        sys.exit(1)
    match = re.search(r'"sesskey"\s*:\s*"([^"]{10,})"', html)
    if not match:
        print("ERROR: Could not get sesskey. Your session may have expired.")
        sys.exit(1)
    return match.group(1)


def ajax(methodname, args=None):
    sesskey = get_sesskey()
    url = f"{BASE}/lib/ajax/service.php?sesskey={sesskey}"
    payload = json.dumps([{"index": 0, "methodname": methodname, "args": args or {}}]).encode()
    response = fetch(url, post_data=payload)
    data = json.loads(response)
    # Handle top-level error (dict response means service-level failure)
    if isinstance(data, dict) and data.get("error"):
        print(f"ERROR: {data.get('message', 'Moodle error')}")
        sys.exit(1)
    if isinstance(data, list) and data[0].get("error"):
        exc = data[0].get("exception", {})
        print(f"ERROR: {exc.get('message', 'Moodle AJAX error')}")
        sys.exit(1)
    return data[0]["data"]


def cmd_deadlines():
    import time
    data = ajax("core_calendar_get_action_events_by_timesort", {
        "limitnum": 10,
        "timesortfrom": int(time.time()),
    })
    events = data.get("events", [])
    if not events:
        print("No upcoming deadlines. You're all caught up! 🎉")
        return
    print("*Upcoming Deadlines:*\n")
    for e in events[:8]:
        name = e.get("name", "Unnamed")
        course = e.get("course", {}).get("fullname", "Unknown course")
        ts = e.get("timesort", e.get("timestart", 0))
        due_dt = datetime.fromtimestamp(ts)
        due_date = due_dt.strftime("%a %b %d")
        days_left = max(0, (due_dt.date() - datetime.now().date()).days)
        if days_left == 0:
            urgency, days_str = "🔴", "due TODAY"
        elif days_left == 1:
            urgency, days_str = "🔴", "due tomorrow"
        elif days_left <= 3:
            urgency, days_str = "🟡", f"{days_left}d away"
        else:
            urgency, days_str = "🟢", f"{days_left}d away"
        print(f"{urgency} *{course}*")
        print(f"   📝 {name}")
        print(f"   ⏰ {due_date} ({days_str})\n")


def cmd_courses():
    data = ajax("core_course_get_enrolled_courses_by_timeline_classification", {
        "classification": "inprogress",
        "limit": 20,
        "offset": 0,
        "sort": "fullname",
    })
    courses = data.get("courses", [])
    if not courses:
        print("No active courses found.")
        return
    print("*Your Active Courses:*\n")
    for c in courses:
        print(f"  📚 {c.get('fullname', 'Unknown')}")


def cmd_announcements():
    courses_data = ajax("core_course_get_enrolled_courses_by_timeline_classification", {
        "classification": "inprogress",
        "limit": 5,
        "offset": 0,
        "sort": "fullname",
    })
    courses = courses_data.get("courses", [])[:5]
    if not courses:
        print("No courses found.")
        return
    # Use REST-style URL for forum fetch (session cookie works for regular pages too)
    sesskey = get_sesskey()
    url = f"{BASE}/lib/ajax/service.php?sesskey={sesskey}"
    payload = json.dumps([{
        "index": 0,
        "methodname": "mod_forum_get_forums_by_courses",
        "args": {"courseids": [c["id"] for c in courses]},
    }]).encode()
    response = fetch(url, post_data=payload)
    result = json.loads(response)
    if isinstance(result, list) and not result[0].get("error"):
        forums = result[0]["data"]
        news_forums = [f for f in forums if f.get("type") == "news"][:5]
        if news_forums:
            print("*Latest Announcements:*\n")
            for f in news_forums:
                course_name = f.get("coursefullname", f.get("course", "Unknown"))
                print(f"  📢 *{course_name}*: {f.get('name', '')}")
            return
    # Fallback: just list courses
    print("*Active Courses (announcements unavailable):*\n")
    for c in courses:
        print(f"  📚 {c.get('fullname', 'Unknown')}")


COMMANDS = {
    "deadlines": cmd_deadlines,
    "courses": cmd_courses,
    "announcements": cmd_announcements,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd in COMMANDS:
        COMMANDS[cmd]()
    else:
        print("Usage: python3 moodle_api.py <deadlines|courses|announcements>")
        sys.exit(1)
