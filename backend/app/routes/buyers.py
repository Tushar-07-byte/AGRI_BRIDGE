from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.buyer import Buyer


router = APIRouter(
    prefix="/api/buyers",
    tags=["Buyers"]
)


@router.get("/")
def get_buyers(db: Session = Depends(get_db)):

    buyers = db.query(Buyer).all()

    return {
        "success": True,
        "count": len(buyers),
        "buyers": [
            {
                "id": buyer.id,
                "name": buyer.name
            }
            for buyer in buyers
        ]
    }