from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, text
from typing import Optional
from datetime import date
import hashlib

from app.core.database import get_db
from app.core.cache import cache
from app.models.db import JeccLog
from app.api.v1.schemas import JeccLog as JeccLogSchema, LogsResponse, HealthResponse

router = APIRouter()


def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from parameters"""
    key_data = f"{prefix}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Test cache
        cache.set("health_check", "test", 10)
        cache_status = "healthy" if cache.get("health_check") == "test" else "unhealthy"
        cache.delete("health_check")
    except Exception:
        cache_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" and cache_status == "healthy" else "unhealthy",
        database=db_status,
        cache=cache_status
    )


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    agency: Optional[str] = Query(None, description="Agency filter"),
    call_type: Optional[str] = Query(None, description="Call type filter"),
    db: Session = Depends(get_db)
):
    """Get logs with pagination and filtering"""
    
    # Generate cache key
    cache_key = generate_cache_key(
        "logs",
        page=page,
        per_page=per_page,
        start_date=start_date,
        end_date=end_date,
        agency=agency,
        call_type=call_type
    )
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return LogsResponse(**cached_result)
    
    # Build query
    query = db.query(JeccLog)
    
    # Apply filters
    filters = []
    if start_date:
        filters.append(JeccLog.log_date >= start_date)
    if end_date:
        filters.append(JeccLog.log_date <= end_date)
    if agency:
        filters.append(JeccLog.agency.ilike(f"%{agency}%"))
    if call_type:
        filters.append(JeccLog.call_type.ilike(f"%{call_type}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    offset = (page - 1) * per_page
    logs = query.order_by(desc(JeccLog.log_date), desc(JeccLog.log_time))\
               .offset(offset)\
               .limit(per_page)\
               .all()
    
    # Calculate pagination info
    has_next = offset + per_page < total
    has_prev = page > 1
    
    result = LogsResponse(
        logs=[JeccLogSchema.model_validate(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev
    )
    
    # Cache the result
    cache.set(cache_key, result.model_dump())
    
    return result


@router.get("/logs/{log_id}", response_model=JeccLogSchema)
async def get_log_by_id(log_id: int, db: Session = Depends(get_db)):
    """Get a specific log by ID"""
    
    # Try cache first
    cache_key = f"log:{log_id}"
    cached_log = cache.get(cache_key)
    if cached_log:
        return JeccLogSchema(**cached_log)
    
    # Query database
    log = db.query(JeccLog).filter(JeccLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    result = JeccLogSchema.model_validate(log)
    
    # Cache the result
    cache.set(cache_key, result.model_dump())
    
    return result


@router.post("/logs/refresh")
async def refresh_logs():
    """Trigger logs refresh and clear cache"""
    cache.clear_pattern("logs:*")
    cache.clear_pattern("log:*")
    
    return {"message": "Cache cleared, logs refresh triggered"}


@router.post("/scraper/run")
async def run_scraper(days: int = 3):
    """Trigger scraper to fetch recent logs"""
    try:
        from app.scraper.jecc_scraper import jecc_scraper
        
        # Run scraper for recent days
        new_logs = jecc_scraper.scrape_recent_days(days)
        
        # Run geocoding for recent logs
        geocoded = jecc_scraper.geocode_recent_logs(20)
        
        return {
            "message": "Scraper completed successfully",
            "new_logs": new_logs,
            "geocoded_logs": geocoded
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper error: {str(e)}")


@router.post("/geocoder/run")
async def run_geocoder(limit: int = 50):
    """Trigger geocoding of existing logs"""
    try:
        from app.scraper.jecc_scraper import jecc_scraper
        
        geocoded = jecc_scraper.geocode_recent_logs(limit)
        
        return {
            "message": "Geocoding completed successfully",
            "geocoded_logs": geocoded
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding error: {str(e)}")