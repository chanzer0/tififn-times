#!/usr/bin/env python3
"""
Script to run the JECC scraper
Usage:
    python scripts/run_scraper.py                    # Scrape last 7 days
    python scripts/run_scraper.py --days 30          # Scrape last 30 days
    python scripts/run_scraper.py --date 2024-01-15  # Scrape specific date
    python scripts/run_scraper.py --geocode-only     # Only geocode existing logs
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from app.scraper.jecc_scraper import jecc_scraper


def main():
    parser = argparse.ArgumentParser(description='Run JECC scraper')
    parser.add_argument('--days', type=int, default=7, help='Number of recent days to scrape')
    parser.add_argument('--date', type=str, help='Specific date to scrape (YYYY-MM-DD)')
    parser.add_argument('--start-date', type=str, help='Start date for range scraping (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for range scraping (YYYY-MM-DD)')
    parser.add_argument('--geocode-only', action='store_true', help='Only geocode existing logs')
    parser.add_argument('--geocode-limit', type=int, default=50, help='Limit for geocoding batch')
    
    args = parser.parse_args()
    
    try:
        if args.geocode_only:
            print(f"Geocoding up to {args.geocode_limit} logs...")
            count = jecc_scraper.geocode_recent_logs(args.geocode_limit)
            print(f"Successfully geocoded {count} logs")
            
        elif args.date:
            # Scrape specific date
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
            print(f"Scraping logs for {target_date.strftime('%m/%d/%Y')}...")
            count = jecc_scraper.scrape_date_range(target_date)
            print(f"Successfully processed {count} new logs")
            
        elif args.start_date and args.end_date:
            # Scrape date range
            start = datetime.strptime(args.start_date, '%Y-%m-%d')
            end = datetime.strptime(args.end_date, '%Y-%m-%d')
            print(f"Scraping logs from {start.strftime('%m/%d/%Y')} to {end.strftime('%m/%d/%Y')}...")
            count = jecc_scraper.scrape_date_range(start, end)
            print(f"Successfully processed {count} new logs")
            
        else:
            # Scrape recent days
            print(f"Scraping logs for the last {args.days} days...")
            count = jecc_scraper.scrape_recent_days(args.days)
            print(f"Successfully processed {count} new logs")
            
            # Also geocode some recent logs
            print("Geocoding recent logs...")
            geocoded = jecc_scraper.geocode_recent_logs(20)
            print(f"Successfully geocoded {geocoded} logs")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scraping: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()