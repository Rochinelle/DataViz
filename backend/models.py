from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database import Base


class Dataset(Base):
    """Dataset model for storing uploaded file metadata"""
    __tablename__ = "datasets"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Relationship with data records
    records = relationship("DataRecord", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, filename={self.filename})>"

class DataRecord(Base):
    """Data record model for storing processed data"""
    __tablename__ = "data_records"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    json_data = Column(Text, nullable=False)  # JSON string of the record
    
    # Relationship with dataset
    dataset = relationship("Dataset", back_populates="records")
    
    def __repr__(self):
        return f"<DataRecord(id={self.id}, dataset_id={self.dataset_id})>"