from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey

from ..database.connection import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    farmer_id = Column(
        Integer,
        ForeignKey("farmers.id"),
        nullable=False
    )

    crop_type = Column(String(100), nullable=False)

    photo_path = Column(String(255), nullable=True)

    health_status = Column(String(100), nullable=True)

    confidence = Column(Numeric(5, 4), nullable=True)

    harvest_date = Column(Date, nullable=True)

    quantity_est = Column(Numeric(10, 2), nullable=True)

    status = Column(
        String(50),
        nullable=True,
        default="available"
    )