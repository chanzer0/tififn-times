from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.models.db import JeccLog
from app.services.geocode import geocoding_service


class LogsService:
    @staticmethod
    def geocode_log(db: Session, log: JeccLog) -> bool:
        """
        Geocode a single log entry
        Returns True if geocoding was successful, False otherwise
        """
        if not log.address or log.latitude is not None:
            return False  # Skip if no address or already geocoded
            
        geocode_result = geocoding_service.geocode_address(log.address)
        if geocode_result:
            lat, lon, formatted_address = geocode_result
            log.latitude = lat
            log.longitude = lon
            log.geocoded_address = formatted_address
            log.geocoded_at = datetime.utcnow()
            
            db.commit()
            return True
            
        return False
    
    @staticmethod
    def geocode_logs_batch(db: Session, limit: int = 10) -> int:
        """
        Geocode a batch of logs that haven't been geocoded yet
        Returns the number of successfully geocoded logs
        """
        # Get logs that need geocoding
        logs_to_geocode = db.query(JeccLog)\
            .filter(JeccLog.address.isnot(None))\
            .filter(JeccLog.latitude.is_(None))\
            .limit(limit)\
            .all()
        
        geocoded_count = 0
        for log in logs_to_geocode:
            if LogsService.geocode_log(db, log):
                geocoded_count += 1
                
        return geocoded_count
    
    @staticmethod
    def get_logs_with_coordinates(db: Session) -> List[JeccLog]:
        """Get all logs that have been geocoded"""
        return db.query(JeccLog)\
            .filter(JeccLog.latitude.isnot(None))\
            .filter(JeccLog.longitude.isnot(None))\
            .all()


logs_service = LogsService()