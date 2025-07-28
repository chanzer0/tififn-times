#!/usr/bin/env python3
"""
Bulk geocoding script for large datasets with resume capability
Designed for processing 138k+ records efficiently
"""

import sys
import os
import argparse
import time
from datetime import datetime
from typing import List, Dict, Optional

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from app.scraper.jecc_scraper import jecc_scraper
from app.core.database import SessionLocal
from app.models.db import JeccLog
from sqlalchemy import func, and_


class BulkGeocoder:
    def __init__(self, batch_size: int = 1000, delay: float = 1.1):
        self.batch_size = batch_size
        self.delay = delay  # Slightly over 1 second for Nominatim
        self.progress_file = "geocoding_progress.txt"
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None
        }
    
    def get_progress(self) -> int:
        """Get the last processed ID from progress file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0
    
    def save_progress(self, last_id: int):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            f.write(str(last_id))
    
    def analyze_dataset(self) -> Dict:
        """Analyze the dataset before geocoding"""
        db = SessionLocal()
        try:
            # Total records
            total_records = db.query(JeccLog).count()
            
            # Records without geocoding
            ungeocode_records = db.query(JeccLog).filter(JeccLog.latitude.is_(None)).count()
            
            # Unique addresses needing geocoding
            unique_addresses = db.query(JeccLog.address)\
                .filter(and_(JeccLog.address.isnot(None), JeccLog.latitude.is_(None)))\
                .distinct().count()
            
            # Most recent ungeocode record
            recent_ungeocode = db.query(func.max(JeccLog.log_date))\
                .filter(JeccLog.latitude.is_(None)).scalar()
            
            return {
                "total_records": total_records,
                "ungeocode_records": ungeocode_records,
                "unique_addresses": unique_addresses,
                "recent_ungeocode": recent_ungeocode,
                "estimated_hours": ungeocode_records * self.delay / 3600
            }
        finally:
            db.close()
    
    def get_unique_addresses_to_process(self, start_id: int, strategy: str = "recent_first", limit: int = None) -> List[str]:
        """Get unique addresses that need geocoding"""
        db = SessionLocal()
        try:
            # Get unique addresses that haven't been geocoded yet
            if strategy == "recent_first":
                # Get the most recent record for each unique address
                subquery = db.query(
                    JeccLog.address,
                    func.max(JeccLog.log_date).label('max_date'),
                    func.max(JeccLog.id).label('max_id')
                ).filter(and_(
                    JeccLog.address.isnot(None),
                    JeccLog.latitude.is_(None),
                    JeccLog.id > start_id
                )).group_by(JeccLog.address).subquery()
                
                query = db.query(subquery.c.address)\
                    .order_by(subquery.c.max_date.desc(), subquery.c.max_id.desc())
            elif strategy == "most_common_first":
                # Get addresses ordered by count of records needing geocoding
                subquery = db.query(
                    JeccLog.address,
                    func.count(JeccLog.id).label('record_count'),
                    func.max(JeccLog.id).label('max_id')
                ).filter(and_(
                    JeccLog.address.isnot(None),
                    JeccLog.latitude.is_(None),
                    JeccLog.id > start_id
                )).group_by(JeccLog.address).subquery()
                
                query = db.query(subquery.c.address)\
                    .order_by(subquery.c.record_count.desc(), subquery.c.max_id.desc())
            else:
                # Get unique addresses ordered by first occurrence
                query = db.query(JeccLog.address)\
                    .filter(and_(
                        JeccLog.address.isnot(None),
                        JeccLog.latitude.is_(None),
                        JeccLog.id > start_id
                    ))\
                    .distinct()\
                    .order_by(JeccLog.address)
            
            actual_limit = limit if limit else self.batch_size
            addresses = query.limit(actual_limit).all()
            return [addr[0] for addr in addresses]
        finally:
            db.close()

    def get_records_for_address(self, address: str) -> List[JeccLog]:
        """Get all records that need geocoding for a specific address"""
        db = SessionLocal()
        try:
            records = db.query(JeccLog)\
                .filter(and_(
                    JeccLog.address == address,
                    JeccLog.latitude.is_(None)
                ))\
                .all()
            return records
        finally:
            db.close()
    
    def process_address_batch(self, addresses: List[str]) -> Dict:
        """Process a batch of unique addresses"""
        batch_stats = {"successful": 0, "failed": 0, "skipped": 0, "addresses_processed": 0, "records_updated": 0}
        
        for address in addresses:
            if not address:
                batch_stats["skipped"] += 1
                continue
                
            print(f"Geocoding address: {address[:60]}...")
            
            # Get all records for this address
            records = self.get_records_for_address(address)
            if not records:
                print(f"   No records found for address: {address}")
                batch_stats["skipped"] += 1
                continue
                
            print(f"   Found {len(records)} records for this address")
            
            # Geocode the address once
            success, result = self.geocode_address_once(address)
            
            if success:
                # Update all records with the same address
                updated_count = self.update_records_with_geocoding(address, result)
                batch_stats["successful"] += 1
                batch_stats["records_updated"] += updated_count
                print(f"✓ Successfully geocoded address, updated {updated_count} records")
            else:
                batch_stats["failed"] += 1
                print(f"✗ Failed to geocode address: {result}")
            
            batch_stats["addresses_processed"] += 1
            
            # Rate limiting (once per address, not per record)
            time.sleep(self.delay)
            
            # Save progress using the highest ID from this address batch
            max_id = max(record.id for record in records)
            self.save_progress(max_id)
        
        return batch_stats

    def geocode_address_once(self, address: str) -> tuple:
        """Geocode a single address and return result"""
        try:
            from app.services.geocode import geocoding_service
            
            # Get geocoding result
            geocode_result = geocoding_service.geocode_address(address)
            
            if geocode_result:
                lat, lon, formatted_address = geocode_result
                return True, (lat, lon, formatted_address)
            else:
                return False, "No geocoding result returned"
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            return False, error_msg

    def update_records_with_geocoding(self, address: str, geocode_result: tuple) -> int:
        """Update all records with the same address with geocoding data"""
        lat, lon, formatted_address = geocode_result
        
        db = SessionLocal()
        try:
            # Update all records with this address that don't have coordinates
            updated = db.query(JeccLog)\
                .filter(and_(
                    JeccLog.address == address,
                    JeccLog.latitude.is_(None)
                ))\
                .update({
                    'latitude': lat,
                    'longitude': lon,
                    'geocoded_address': formatted_address,
                    'geocoded_at': datetime.utcnow()
                })
            
            db.commit()
            return updated
        except Exception as e:
            print(f"   Error updating records: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def geocode_single_record(self, db, record: JeccLog):
        """Geocode a single record"""
        try:
            from app.services.geocode import geocoding_service
            
            # Get geocoding result
            geocode_result = geocoding_service.geocode_address(record.address)
            
            if geocode_result:
                lat, lon, formatted_address = geocode_result
                
                # Update the record
                old_lat = record.latitude
                record.latitude = lat
                record.longitude = lon
                record.geocoded_address = formatted_address
                record.geocoded_at = datetime.utcnow()
                
                print(f"   DB UPDATE: Setting lat={lat}, lon={lon} (was {old_lat})")
                db.commit()
                print(f"   DB COMMITTED for ID {record.id}")
                
                return True, "Success"
            else:
                return False, "No geocoding result returned"
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"   Error geocoding: {error_msg}")
            db.rollback()
            return False, error_msg
    
    def run_bulk_geocoding(self, strategy: str = "recent_first", max_records: Optional[int] = None):
        """Run the bulk geocoding process"""
        print("🚀 Starting bulk geocoding process...")
        
        # Analyze dataset
        analysis = self.analyze_dataset()
        print(f"\n📊 Dataset Analysis:")
        print(f"   Total records: {analysis['total_records']:,}")
        print(f"   Need geocoding: {analysis['ungeocode_records']:,}")
        print(f"   Unique addresses: {analysis['unique_addresses']:,}")
        print(f"   Estimated time: {analysis['estimated_hours']:.1f} hours")
        
        # Get starting point
        start_id = self.get_progress()
        print(f"\n📍 Resuming from ID: {start_id}")
        
        self.stats["start_time"] = datetime.now()
        total_processed = 0
        
        while True:
            if max_records and total_processed >= max_records:
                print(f"\n🛑 Reached maximum records limit: {max_records}")
                break
            
            # Calculate remaining addresses to process
            remaining = max_records - total_processed if max_records else None
            batch_limit = min(remaining, self.batch_size) if remaining else None
            
            # Get batch of unique addresses
            addresses = self.get_unique_addresses_to_process(start_id, strategy, batch_limit)
            
            if not addresses:
                print("\n✅ No more addresses to process!")
                break
            
            print(f"\n🔄 Processing batch: {len(addresses)} unique addresses")
            
            # Process address batch
            batch_stats = self.process_address_batch(addresses)
            
            # Update stats
            self.stats["processed"] += batch_stats["addresses_processed"]
            self.stats["successful"] += batch_stats["successful"]
            self.stats["failed"] += batch_stats["failed"]
            self.stats["skipped"] += batch_stats["skipped"]
            
            total_processed += batch_stats["addresses_processed"]
            
            # Update start_id based on highest processed record ID
            start_id = self.get_progress()
            
            # Progress report
            elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
            rate = self.stats["processed"] / elapsed if elapsed > 0 else 0
            remaining = analysis["ungeocode_records"] - total_processed
            eta_hours = remaining / (rate * 3600) if rate > 0 else 0
            
            print(f"\n📈 Progress Report:")
            print(f"   Addresses processed: {self.stats['processed']:,}")
            print(f"   Successfully geocoded: {self.stats['successful']:,}")
            print(f"   Failed: {self.stats['failed']:,}")
            print(f"   Records updated: {batch_stats.get('records_updated', 0):,}")
            print(f"   Rate: {rate:.2f} addresses/sec")
            print(f"   ETA: {eta_hours:.1f} hours")
        
        print(f"\n🎉 Bulk geocoding completed!")
        print(f"Final stats: {self.stats}")


def main():
    parser = argparse.ArgumentParser(description='Bulk geocode emergency call records')
    parser.add_argument('--strategy', choices=['recent_first', 'oldest_first', 'id_order', 'most_common_first'], 
                       default='recent_first', help='Processing strategy (most_common_first maximizes records updated per API call)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size')
    parser.add_argument('--max-records', type=int, help='Maximum records to process (for testing)')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze dataset')
    parser.add_argument('--reset-progress', action='store_true', help='Reset progress and exit')
    
    args = parser.parse_args()
    
    geocoder = BulkGeocoder(batch_size=args.batch_size)
    
    if args.reset_progress:
        if os.path.exists(geocoder.progress_file):
            os.remove(geocoder.progress_file)
            print("🔄 Progress reset!")
        else:
            print("📄 No progress file found.")
        return
    
    if args.analyze_only:
        analysis = geocoder.analyze_dataset()
        print("📊 Dataset Analysis:")
        for key, value in analysis.items():
            print(f"   {key}: {value}")
        return
    
    try:
        geocoder.run_bulk_geocoding(args.strategy, args.max_records)
    except KeyboardInterrupt:
        print("\n⏸️  Process interrupted. Progress saved. Resume with the same command.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Progress saved. You can resume the process.")


if __name__ == "__main__":
    main()