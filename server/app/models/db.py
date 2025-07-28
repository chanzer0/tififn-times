from sqlalchemy import Column, Integer, String, Date, Time, Text, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class JeccLog(Base):
    __tablename__ = "jecc_logs"

    id = Column(Integer, primary_key=True, index=True)
    cfs_number = Column(Integer, nullable=True, index=True)
    address = Column(Text, nullable=True)
    call_type = Column(Text, nullable=True)
    log_date = Column(Date, nullable=False, index=True)
    log_time = Column(Time, nullable=True)
    apt_suite = Column(Text, nullable=True)
    agency = Column(Text, nullable=True)
    disposition = Column(Text, nullable=True)
    incident_number = Column(Text, nullable=True)
    
    # New columns for geocoding
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    geocoded_at = Column(DateTime(timezone=True), nullable=True)
    geocoded_address = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<JeccLog(id={self.id}, cfs_number={self.cfs_number}, address='{self.address}')>"