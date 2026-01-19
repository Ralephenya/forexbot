"""
Major News Event Filter for Forex Trading
Identifies and filters out major news events that cause unpredictable volatility
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_major_news_events_2024():
    """
    Get major news events for June-December 2024
    
    Returns:
        List of datetime objects (UTC) for major news releases
    """
    events = []
    
    # US Non-Farm Payrolls (NFP) - First Friday of each month
    # NFP is typically released at 8:30 AM ET (12:30 UTC or 13:30 UTC depending on DST)
    nfp_dates = [
        datetime(2024, 6, 7, 12, 30, tzinfo=timezone.utc),   # June NFP
        datetime(2024, 7, 5, 12, 30, tzinfo=timezone.utc),   # July NFP
        datetime(2024, 8, 2, 12, 30, tzinfo=timezone.utc),   # August NFP
        datetime(2024, 9, 6, 12, 30, tzinfo=timezone.utc),   # September NFP
        datetime(2024, 10, 4, 12, 30, tzinfo=timezone.utc),  # October NFP
        datetime(2024, 11, 1, 13, 30, tzinfo=timezone.utc),  # November NFP (DST starts)
        datetime(2024, 12, 6, 13, 30, tzinfo=timezone.utc),  # December NFP
    ]
    events.extend([('NFP', dt) for dt in nfp_dates])
    
    # FOMC Meeting Dates (Federal Reserve)
    # FOMC decisions typically at 2:00 PM ET (18:00 UTC or 19:00 UTC)
    fomc_dates = [
        datetime(2024, 6, 12, 18, 0, tzinfo=timezone.utc),   # June FOMC
        datetime(2024, 7, 31, 18, 0, tzinfo=timezone.utc),   # July FOMC
        datetime(2024, 9, 18, 18, 0, tzinfo=timezone.utc),   # September FOMC
        datetime(2024, 11, 7, 19, 0, tzinfo=timezone.utc),   # November FOMC (DST)
        datetime(2024, 12, 18, 19, 0, tzinfo=timezone.utc),  # December FOMC
    ]
    events.extend([('FOMC', dt) for dt in fomc_dates])
    
    # ECB Interest Rate Decisions
    # ECB decisions typically at 1:15 PM CET (12:15 UTC or 13:15 UTC)
    ecb_dates = [
        datetime(2024, 6, 6, 12, 15, tzinfo=timezone.utc),   # June ECB
        datetime(2024, 7, 18, 12, 15, tzinfo=timezone.utc),  # July ECB
        datetime(2024, 9, 12, 12, 15, tzinfo=timezone.utc),  # September ECB
        datetime(2024, 10, 17, 12, 15, tzinfo=timezone.utc), # October ECB
        datetime(2024, 12, 12, 13, 15, tzinfo=timezone.utc), # December ECB
    ]
    events.extend([('ECB', dt) for dt in ecb_dates])
    
    # US CPI (Consumer Price Index) - Typically mid-month
    # CPI typically released at 8:30 AM ET (12:30 UTC or 13:30 UTC)
    cpi_dates = [
        datetime(2024, 6, 12, 12, 30, tzinfo=timezone.utc),  # June CPI
        datetime(2024, 7, 11, 12, 30, tzinfo=timezone.utc),  # July CPI
        datetime(2024, 8, 14, 12, 30, tzinfo=timezone.utc),  # August CPI
        datetime(2024, 9, 11, 12, 30, tzinfo=timezone.utc),  # September CPI
        datetime(2024, 10, 10, 12, 30, tzinfo=timezone.utc), # October CPI
        datetime(2024, 11, 14, 13, 30, tzinfo=timezone.utc), # November CPI (DST)
        datetime(2024, 12, 12, 13, 30, tzinfo=timezone.utc), # December CPI
    ]
    events.extend([('CPI', dt) for dt in cpi_dates])
    
    # US GDP (Quarterly) - Preliminary and Final releases
    # GDP typically at 8:30 AM ET
    gdp_dates = [
        datetime(2024, 6, 27, 12, 30, tzinfo=timezone.utc),  # Q1 2024 Final
        datetime(2024, 7, 25, 12, 30, tzinfo=timezone.utc),  # Q2 2024 Preliminary
        datetime(2024, 9, 26, 12, 30, tzinfo=timezone.utc),  # Q2 2024 Final
        datetime(2024, 10, 30, 13, 30, tzinfo=timezone.utc), # Q3 2024 Preliminary (DST)
        datetime(2024, 12, 19, 13, 30, tzinfo=timezone.utc), # Q3 2024 Final
    ]
    events.extend([('GDP', dt) for dt in gdp_dates])
    
    # Major Central Bank Speeches (ECB President, Fed Chair)
    # These are less predictable but add important events
    speech_dates = [
        datetime(2024, 6, 5, 14, 0, tzinfo=timezone.utc),    # ECB Press Conference (after meeting)
        datetime(2024, 7, 2, 14, 0, tzinfo=timezone.utc),    # ECB Press Conference
        datetime(2024, 9, 12, 14, 0, tzinfo=timezone.utc),   # ECB Press Conference
        datetime(2024, 12, 12, 14, 15, tzinfo=timezone.utc), # ECB Press Conference
        datetime(2024, 6, 12, 18, 30, tzinfo=timezone.utc),  # Fed Press Conference (after FOMC)
        datetime(2024, 7, 31, 18, 30, tzinfo=timezone.utc),  # Fed Press Conference
        datetime(2024, 9, 18, 18, 30, tzinfo=timezone.utc),  # Fed Press Conference
        datetime(2024, 11, 7, 19, 30, tzinfo=timezone.utc),  # Fed Press Conference
        datetime(2024, 12, 18, 19, 30, tzinfo=timezone.utc), # Fed Press Conference
    ]
    events.extend([('SPEECH', dt) for dt in speech_dates])
    
    return events


def is_news_event_time(dt, events, hours_before=1, hours_after=2):
    """
    Check if a datetime falls within the news event filter window
    
    Args:
        dt: datetime to check
        events: List of (event_type, datetime) tuples
        hours_before: Hours before news to filter (default: 1)
        hours_after: Hours after news to filter (default: 2)
    
    Returns:
        (bool, event_info): (True if filtered, event_info dict)
    """
    dt = pd.to_datetime(dt, utc=True)
    
    for event_type, event_dt in events:
        window_start = event_dt - timedelta(hours=hours_before)
        window_end = event_dt + timedelta(hours=hours_after)
        
        if window_start <= dt <= window_end:
            return True, {
                'event_type': event_type,
                'event_time': event_dt,
                'window_start': window_start,
                'window_end': window_end
            }
    
    return False, None


def filter_news_events(df, events=None, hours_before=1, hours_after=2):
    """
    Add news filter column to dataframe
    
    Args:
        df: DataFrame with 'datetime' column
        events: List of (event_type, datetime) tuples (if None, uses default)
        hours_before: Hours before news to filter
        hours_after: Hours after news to filter
    
    Returns:
        DataFrame with 'news_filter' boolean column (True = filtered out)
    """
    if events is None:
        events = get_major_news_events_2024()
    
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Apply news filter
    df['news_filter'] = df['datetime'].apply(
        lambda dt: is_news_event_time(dt, events, hours_before, hours_after)[0]
    )
    
    return df


def print_news_events(events=None):
    """Print news events calendar"""
    if events is None:
        events = get_major_news_events_2024()
    
    print("\n" + "=" * 70)
    print("MAJOR NEWS EVENTS (June-December 2024)")
    print("=" * 70)
    
    # Group by event type
    events_by_type = {}
    for event_type, event_dt in events:
        if event_type not in events_by_type:
            events_by_type[event_type] = []
        events_by_type[event_type].append(event_dt)
    
    for event_type in sorted(events_by_type.keys()):
        print(f"\n{event_type}:")
        for event_dt in sorted(events_by_type[event_type]):
            print(f"  {event_dt.strftime('%Y-%m-%d %H:%M UTC')}")
    
    print("\n" + "=" * 70)
    print(f"Total Events: {len(events)}")
    print("=" * 70)


def main():
    """Test news filter"""
    print_news_events()
    
    # Test filter on sample data
    sample_dates = [
        datetime(2024, 6, 7, 11, 30, tzinfo=timezone.utc),  # 1 hour before NFP (FILTERED)
        datetime(2024, 6, 7, 12, 30, tzinfo=timezone.utc),  # NFP release time (FILTERED)
        datetime(2024, 6, 7, 14, 30, tzinfo=timezone.utc),  # 2 hours after NFP (FILTERED)
        datetime(2024, 6, 7, 15, 0, tzinfo=timezone.utc),   # 2.5 hours after (NOT FILTERED)
        datetime(2024, 6, 8, 12, 0, tzinfo=timezone.utc),   # Normal trading (NOT FILTERED)
    ]
    
    events = get_major_news_events_2024()
    print("\n" + "=" * 70)
    print("NEWS FILTER TEST")
    print("=" * 70)
    for dt in sample_dates:
        is_filtered, event_info = is_news_event_time(dt, events)
        status = "FILTERED" if is_filtered else "ALLOWED"
        event_str = f" ({event_info['event_type']})" if event_info else ""
        print(f"{dt.strftime('%Y-%m-%d %H:%M UTC')}: {status}{event_str}")
    print("=" * 70)


if __name__ == "__main__":
    main()

