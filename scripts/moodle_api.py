#!/usr/bin/env python3
"""
Moodle REST API helper for AUM (online.aum.edu.mn).
Usage: python3 moodle_api.py <command>
Commands: deadlines | courses | announcements
Token read from: ~/personal-bot/data/moodle-token.txt
"""
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

BASE_URL = "https://online.aum.edu.mn/webservice/rest/server.php"
TOKEN_FILE = Path.home() / "personal-bot" / "data" / "moodle-token.txt"


def get_token():
    if not TOKEN_FILE.exists():
        print("ERROR: No Moodle token found. Tell the user to run 'setup moodle'.")
        sys.exit(1)
    token = TOKEN_FILE.read_text().strip()
    if not token:
        print("ERROR: Moodle token file is empty. Run 'setup moodle' to set it.")
        sys.exit(1)
    return token


def api_call(wsfunction, params=None):
    token = get_token()
    query = {"wstoken": token, "wsfunction": wsfunction, "moodlewsrestformat": "json"}
    if params:
        query.update(params)
    url = BASE_URL + "?" + urllib.parse.urlencode(query)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"ERROR: Could not reach Moodle. Check your internet connection. ({e})")
        sys.exit(1)
    if isinstance(data, dict) and "exception" in data:
        msg = data.get("message", "Moodle API error")
        print(f"ERROR: {msg}")
        sys.exit(1)
    return data


def cmd_deadlines():
    data = api_call("core_calendar_get_calendar_upcoming_view")
    events = data.get("events", [])
    if not events:
        print("No upcoming deadlines. You're all caught up! 🎉")
        return
    print("*Upcoming Deadlines:*\n")
    for e in events[:8]:  # cap at 8 to keep Telegram response short
        name = e.get("name", "Unnamed")
        course = e.get("course", {}).get("fullname", "Unknown course")
        ts = e.get("timestart", 0)
        due_dt = datetime.fromtimestamp(ts)
        due_date = due_dt.strftime("%a %b %d")
        days_left = max(0, (due_dt.date() - datetime.now().date()).days)
        if days_left == 0:
            urgency = "🔴"
            days_str = "due TODAY"
        elif days_left == 1:
            urgency = "🔴"
            days_str = "due tomorrow"
        elif days_left <= 3:
            urgency = "🟡"
            days_str = f"{days_left}d away"
        else:
            urgency = "🟢"
            days_str = f"{days_left}d away"
        print(f"{urgency} *{course}*")
        print(f"   📝 {name}")
        print(f"   ⏰ {due_date} ({days_str})\n")


def cmd_courses():
    data = api_call(
        "core_course_get_enrolled_courses_by_timeline_classification",
        {"classification": "inprogress"},
    )
    courses = data.get("courses", [])
    if not courses:
        print("No active courses found.")
        return
    print("*Your Active Courses:*\n")
    for c in courses:
        print(f"  📚 {c.get('fullname', 'Unknown')}")


def cmd_announcements():
    # Step 1: get enrolled course IDs
    courses_data = api_call(
        "core_course_get_enrolled_courses_by_timeline_classification",
        {"classification": "inprogress"},
    )
    courses = courses_data.get("courses", [])[:5]
    if not courses:
        print("No courses found to check announcements.")
        return
    params = {f"courseids[{i}]": c["id"] for i, c in enumerate(courses)}
    forums = api_call("mod_forum_get_forums_by_courses", params)
    # News forums are the announcement forums in Moodle
    news_forums = [f for f in forums if f.get("type") == "news"][:5]
    if not news_forums:
        print("No announcement forums found in your active courses.")
        return
    print("*Latest Announcements:*\n")
    for f in news_forums:
        course_name = f.get("course", "Unknown course")
        forum_name = f.get("name", "")
        print(f"  📢 *{course_name}*: {forum_name}")


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
