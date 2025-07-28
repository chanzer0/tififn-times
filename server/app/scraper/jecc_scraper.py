import requests
import bs4
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.db import JeccLog
from app.services.geocode import geocoding_service
from app.core.cache import cache


class JeccScraper:
    def __init__(self):
        self.jecc_url = settings.jecc_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TiffinTimes/1.0 (emergency-logs-scraper)'
        })

    def fetch_jecc_logs(self, selected_date: datetime, selected_agency: str = "All") -> str:
        """Fetch logs from JECC for a given date and agency."""
        data = {
            "SelectedDate": selected_date.strftime("%m/%d/%Y"),
            "SelectedAgency": selected_agency,
            "Submit": "Select",
        }
        
        try:
            response = self.session.post(self.jecc_url, data=data, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching logs for {selected_date.strftime('%m/%d/%Y')}: {e}")
            return ""

    def parse_jecc_logs(self, logs_html: str) -> List[Dict]:
        """Parse logs from JECC HTML content."""
        soup = bs4.BeautifulSoup(logs_html, "html.parser")
        post_content = soup.find("div", class_="art-PostContent")

        if not post_content:
            print("Couldn't find div with class 'art-PostContent'")
            return []

        inner_table = post_content.find("table")
        if inner_table:
            inner_table = inner_table.find("table")
        if not inner_table:
            print("Couldn't find the inner table")
            return []

        parsed_logs = []
        for row in inner_table.find_all("tr"):
            log_entry = self._parse_log_row(row)
            if log_entry and log_entry.get("CFS #"):  # Only include valid entries
                parsed_logs.append(log_entry)
        
        return parsed_logs

    def _parse_log_row(self, row) -> Dict:
        """Parse a single row of the log table into a dictionary."""
        cells = row.find_all("td")
        if len(cells) < 6:  # Need at least 6 cells for valid data
            return {}
            
        log_entry = {}
        separated_cell_list = [
            cell.get_text(separator="<br/>", strip=True).split("<br/>")
            for cell in cells[1::2]
        ]

        if len(separated_cell_list) < 3:
            return {}

        # Parse CFS number
        try:
            cfs_text = separated_cell_list[0][0].strip()
            log_entry["CFS #"] = int(cfs_text) if cfs_text.isdigit() else None
        except (ValueError, IndexError):
            log_entry["CFS #"] = None

        # Parse address and call type
        log_entry["Address"] = (
            separated_cell_list[0][1].strip() if len(separated_cell_list[0]) > 1 else None
        )
        log_entry["Call Type"] = (
            separated_cell_list[0][2].strip() if len(separated_cell_list[0]) > 2 else None
        )

        # Parse time
        time_str = separated_cell_list[1][0].strip() if len(separated_cell_list[1]) > 0 else None
        if time_str:
            try:
                log_entry["Time"] = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                try:
                    # Try 12-hour format as well
                    log_entry["Time"] = datetime.strptime(time_str, "%I:%M %p").time()
                except ValueError:
                    log_entry["Time"] = None
        else:
            log_entry["Time"] = None

        # Parse apt/suite
        log_entry["Apt/Suite"] = (
            separated_cell_list[1][1].strip() if len(separated_cell_list[1]) > 1 else None
        )

        # Parse agency and disposition
        log_entry["Agency"] = (
            separated_cell_list[2][0].strip() if len(separated_cell_list[2]) > 0 else None
        )
        log_entry["Disposition"] = (
            separated_cell_list[2][1].strip() if len(separated_cell_list[2]) > 1 else None
        )
        log_entry["Incident #"] = (
            separated_cell_list[2][2].strip() if len(separated_cell_list[2]) > 2 else None
        )

        return log_entry

    def upsert_logs_to_database(self, logs_data: List[Dict], log_date: datetime) -> int:
        """Upsert logs to database using SQLAlchemy."""
        if not logs_data:
            return 0

        db = SessionLocal()
        inserted_count = 0
        
        try:
            for log_data in logs_data:
                if not log_data.get("CFS #"):
                    continue
                    
                # Check if log already exists
                existing_log = db.query(JeccLog).filter(
                    JeccLog.cfs_number == log_data["CFS #"],
                    JeccLog.log_date == log_date.date()
                ).first()

                if existing_log:
                    # Update existing log
                    existing_log.address = log_data.get("Address")
                    existing_log.call_type = log_data.get("Call Type")
                    existing_log.log_time = log_data.get("Time")
                    existing_log.apt_suite = log_data.get("Apt/Suite")
                    existing_log.agency = log_data.get("Agency")
                    existing_log.disposition = log_data.get("Disposition")
                    existing_log.incident_number = log_data.get("Incident #")
                    existing_log.updated_at = datetime.utcnow()
                else:
                    # Create new log
                    new_log = JeccLog(
                        cfs_number=log_data["CFS #"],
                        address=log_data.get("Address"),
                        call_type=log_data.get("Call Type"),
                        log_date=log_date.date(),
                        log_time=log_data.get("Time"),
                        apt_suite=log_data.get("Apt/Suite"),
                        agency=log_data.get("Agency"),
                        disposition=log_data.get("Disposition"),
                        incident_number=log_data.get("Incident #")
                    )
                    
                    # Check if we already have geocoding for this address
                    if new_log.address:
                        existing_geocoded = db.query(JeccLog)\
                            .filter(JeccLog.address == new_log.address)\
                            .filter(JeccLog.latitude.isnot(None))\
                            .first()
                        
                        if existing_geocoded:
                            # Copy geocoding data from existing record
                            new_log.latitude = existing_geocoded.latitude
                            new_log.longitude = existing_geocoded.longitude
                            new_log.geocoded_address = existing_geocoded.geocoded_address
                            new_log.geocoded_at = datetime.utcnow()
                            print(f"   ✓ Reused geocoding for: {new_log.address}")
                    
                    db.add(new_log)
                    inserted_count += 1

            db.commit()
            print(f"Processed {len(logs_data)} logs for {log_date.strftime('%m/%d/%Y')} ({inserted_count} new)")
            
            # Clear cache after updating data
            cache.clear_pattern("logs:*")
            
            return inserted_count
            
        except Exception as e:
            db.rollback()
            print(f"Error during database operation for {log_date}: {e}")
            return 0
        finally:
            db.close()

    def geocode_recent_logs(self, limit: int = 10) -> int:
        """Geocode recent logs that haven't been geocoded yet."""
        db = SessionLocal()
        geocoded_count = 0
        
        try:
            # Get logs that need geocoding
            logs_to_geocode = db.query(JeccLog)\
                .filter(JeccLog.address.isnot(None))\
                .filter(JeccLog.latitude.is_(None))\
                .order_by(JeccLog.created_at.desc())\
                .limit(limit)\
                .all()
            
            for log in logs_to_geocode:
                if not log.address:
                    continue
                    
                print(f"Geocoding: {log.address}")
                geocode_result = geocoding_service.geocode_address(log.address)
                
                if geocode_result:
                    lat, lon, formatted_address = geocode_result
                    log.latitude = lat
                    log.longitude = lon
                    log.geocoded_address = formatted_address
                    log.geocoded_at = datetime.utcnow()
                    geocoded_count += 1
                    print(f"✓ Geocoded: {lat}, {lon}")
                else:
                    print(f"✗ Failed to geocode: {log.address}")
            
            if geocoded_count > 0:
                db.commit()
                # Clear cache after geocoding
                cache.clear_pattern("logs:*")
                cache.clear_pattern("log:*")
                
            print(f"Geocoded {geocoded_count} logs")
            return geocoded_count
            
        except Exception as e:
            db.rollback()
            print(f"Error during geocoding: {e}")
            return 0
        finally:
            db.close()

    def scrape_date_range(self, start_date: datetime, end_date: Optional[datetime] = None) -> int:
        """Scrape logs for a date range."""
        if end_date is None:
            end_date = start_date
            
        total_inserted = 0
        current_date = start_date
        
        while current_date <= end_date:
            print(f"Scraping {current_date.strftime('%m/%d/%Y')}...")
            
            logs_html = self.fetch_jecc_logs(current_date)
            if not logs_html.strip():
                print(f"No data found for {current_date.strftime('%m/%d/%Y')}")
                current_date += timedelta(days=1)
                continue

            logs_data = self.parse_jecc_logs(logs_html)
            if not logs_data:
                print(f"No logs parsed for {current_date.strftime('%m/%d/%Y')}")
                current_date += timedelta(days=1)
                continue

            inserted = self.upsert_logs_to_database(logs_data, current_date)
            total_inserted += inserted
            
            current_date += timedelta(days=1)
            
        return total_inserted

    def scrape_recent_days(self, days: int = 7) -> int:
        """Scrape logs for the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        return self.scrape_date_range(start_date, end_date)


# Global scraper instance
jecc_scraper = JeccScraper()