from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time_context(user_timezone="UTC"):
    """
    Get current time information for the coach.
    
    Args:
        user_timezone (str): User's timezone string (e.g., 'Europe/Paris', 'America/New_York')
                            Defaults to 'UTC' if not provided.
    
    Returns:
        dict: Time information in the user's timezone
    """
    # Use UTC as base time
    now_utc = datetime.now(ZoneInfo("UTC"))
    
    # Handle empty or invalid timezone
    if not user_timezone or user_timezone.strip() == "":
        user_timezone = "UTC"
    
    # Convert to user's timezone
    try:
        now = now_utc.astimezone(ZoneInfo(user_timezone))
    except Exception:
        # Fallback to UTC if timezone is invalid
        now = now_utc
        user_timezone = "UTC"
    
    time_of_day = (
        "morning" if 5 <= now.hour < 12
        else "afternoon" if 12 <= now.hour < 17
        else "evening" if 17 <= now.hour < 22
        else "night"
    )
    
    # Get timestamp and day info for operations
    timestamp = now.timestamp()
    day_of_week = now.weekday()  # 0-6 (Monday is 0)
    day_of_month = now.day
    day_of_year = now.timetuple().tm_yday
    week_of_year = now.isocalendar()[1]
    
    # Time formatting options
    time_12h = now.strftime("%I:%M %p")
    time_24h = now.strftime("%H:%M")
    
    return {
        "time_of_day": time_of_day,
        "weekday": now.strftime("%A"),
        "weekday_num": day_of_week,
        "date": now.strftime("%Y-%m-%d"),
        "formatted_date": now.isoformat(),
        "time": time_24h,
        "time_12h": time_12h,
        "time_24h": time_24h,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "timestamp": timestamp,
        "day_of_month": day_of_month,
        "day_of_year": day_of_year,
        "week_of_year": week_of_year,
        "month": now.month,
        "year": now.year,
        "timezone": user_timezone,
        "utc_offset": now.utcoffset().total_seconds() // 3600,
        "utc_offset_minutes": now.utcoffset().total_seconds() // 60,
        "is_dst": now.dst().total_seconds() > 0,
        "utc_time": now_utc.strftime("%H:%M"),
        "utc_date": now_utc.strftime("%Y-%m-%d")
    }