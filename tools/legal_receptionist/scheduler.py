"""
Google Calendar scheduling for legal receptionist consultations.

Uses a demo calendar (not Jon's personal). Creates events with structured
intake data in the description.

Pattern: tools/progress_os/calendar_sync.py
"""

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta

NPX_PATH = shutil.which("npx") or r"C:\Program Files\nodejs\npx.cmd"

# Demo calendar ID — uses primary for now; swap to a dedicated calendar for production
CALENDAR_ID = "primary"


def _run_calendar(args_list):
    """Run a Google Workspace CLI calendar command and return parsed JSON."""
    cmd = [NPX_PATH, "@googleworkspace/cli"] + args_list
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=30, shell=(os.name == "nt")
    )
    if result.returncode != 0:
        raise RuntimeError(f"Calendar CLI error: {result.stderr.strip()}")
    output = result.stdout.strip()
    for i, ch in enumerate(output):
        if ch in "{[":
            try:
                return json.loads(output[i:])
            except json.JSONDecodeError:
                continue
    return None


def _tz_offset():
    """Get local timezone offset string (e.g., '-04:00')."""
    now = datetime.now()
    utc_now = datetime.utcnow()
    delta = now - utc_now
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(abs(total_seconds), 3600)
    minutes = remainder // 60
    sign = "+" if total_seconds >= 0 else "-"
    return f"{sign}{hours:02d}:{minutes:02d}"


def get_available_slots(days_ahead=5, duration_minutes=30):
    """Get available consultation slots for the next N business days.

    Returns list of {"date": "YYYY-MM-DD", "day": "Monday", "slots": ["10:00 AM", ...]}
    """
    tz = _tz_offset()
    now = datetime.now()
    available = []

    # Check each of the next N days
    for day_offset in range(1, days_ahead + 7):
        day = now + timedelta(days=day_offset)

        # Skip weekends
        if day.weekday() >= 5:  # Saturday = 5, Sunday = 6
            continue

        # Friday closes at 4pm, others at 5pm
        close_hour = 16 if day.weekday() == 4 else 17

        # Get existing events for this day
        time_min = day.replace(hour=9, minute=0, second=0).strftime(f"%Y-%m-%dT%H:%M:%S{tz}")
        time_max = day.replace(hour=close_hour, minute=0, second=0).strftime(f"%Y-%m-%dT%H:%M:%S{tz}")

        try:
            result = _run_calendar([
                "calendar", "events", "list",
                "--params", json.dumps({
                    "calendarId": CALENDAR_ID,
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": True,
                    "orderBy": "startTime",
                }),
            ])
        except RuntimeError:
            result = None

        # Build busy times
        busy = []
        if result and result.get("items"):
            for item in result["items"]:
                start = item.get("start", {}).get("dateTime", "")
                end = item.get("end", {}).get("dateTime", "")
                if start and end:
                    busy.append((
                        datetime.fromisoformat(start.replace("Z", "+00:00")),
                        datetime.fromisoformat(end.replace("Z", "+00:00")),
                    ))

        # Generate 30-min slots from 9am to close, skipping busy
        slots = []
        slot_time = day.replace(hour=9, minute=0, second=0)
        end_time = day.replace(hour=close_hour, minute=0, second=0)

        while slot_time + timedelta(minutes=duration_minutes) <= end_time:
            slot_end = slot_time + timedelta(minutes=duration_minutes)
            is_free = True
            for busy_start, busy_end in busy:
                bs = busy_start.replace(tzinfo=None)
                be = busy_end.replace(tzinfo=None)
                if slot_time < be and slot_end > bs:
                    is_free = False
                    break
            if is_free:
                slots.append(slot_time.strftime("%I:%M %p").lstrip("0"))
            slot_time += timedelta(minutes=30)

        if slots:
            available.append({
                "date": day.strftime("%Y-%m-%d"),
                "day": day.strftime("%A"),
                "slots": slots,
            })

        if len(available) >= days_ahead:
            break

    return available


def book_consultation(date_str, time_str, caller_name, practice_area,
                      attorney_name, matter_summary="", phone="", email="",
                      format_type="In-Office", duration_minutes=30):
    """Book a consultation on Google Calendar.

    Args:
        date_str: "YYYY-MM-DD"
        time_str: "10:00 AM" or "2:30 PM"
        caller_name: Client name
        practice_area: Type of matter
        attorney_name: Assigned attorney
        matter_summary: Brief description
        phone: Client phone
        email: Client email
        format_type: "In-Office", "Video (Zoom)", or "Phone"
        duration_minutes: Default 30

    Returns:
        dict with event details
    """
    tz = _tz_offset()

    # Parse the time
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
    end_dt = dt + timedelta(minutes=duration_minutes)

    start_iso = dt.strftime(f"%Y-%m-%dT%H:%M:%S{tz}")
    end_iso = end_dt.strftime(f"%Y-%m-%dT%H:%M:%S{tz}")

    description = (
        f"INTAKE CONSULTATION\n"
        f"{'=' * 30}\n"
        f"Client: {caller_name}\n"
        f"Phone: {phone}\n"
        f"Email: {email}\n"
        f"Practice Area: {practice_area}\n"
        f"Format: {format_type}\n"
        f"{'=' * 30}\n"
        f"Matter Summary:\n{matter_summary}\n"
        f"{'=' * 30}\n"
        f"Booked by: AI Receptionist"
    )

    event = {
        "summary": f"[INTAKE] {caller_name} - {practice_area}",
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": "America/New_York"},
        "end": {"dateTime": end_iso, "timeZone": "America/New_York"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 15},
            ],
        },
    }

    result = _run_calendar([
        "calendar", "events", "insert",
        "--params", json.dumps({"calendarId": CALENDAR_ID}),
        "--body", json.dumps(event),
    ])

    return {
        "event_id": result.get("id", "") if result else "",
        "date": date_str,
        "time": time_str,
        "attorney": attorney_name,
        "format": format_type,
        "link": result.get("htmlLink", "") if result else "",
    }
