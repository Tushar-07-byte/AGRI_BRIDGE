"""
=============================================================================
AGRIBRIDGE DEMO USER SEEDER
=============================================================================
Seeds deterministic demo accounts for judges and evaluators:
1. Farmer:      Mobile: 9876500001 | Password: SecurePassword@123
2. Field Agent: Mobile: 9876500002 | Password: SecurePassword@123
3. Buyer / FPO: Mobile: 9876500003 | Password: SecurePassword@123
4. Admin:       Mobile: 9876500004 | Password: SecurePassword@123
=============================================================================
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from backend.app.database.connection import SessionLocal
from backend.app.models.user import User
from backend.app.models.farmer import Farmer
from backend.app.models.buyer import Buyer
from backend.app.services.auth_service import hash_password, normalize_mobile


def seed_demo_users():
    db = SessionLocal()
    try:
        demo_users = [
            {"mobile": "9876500001", "name": "Ramesh Patel (Farmer)", "role": "farmer"},
            {"mobile": "9876500002", "name": "Priya Sharma (Field Agent)", "role": "field-agent"},
            {"mobile": "9876500003", "name": "ITC Agri Hub (Buyer)", "role": "buyer"},
            {"mobile": "9876500004", "name": "AgriBridge Admin", "role": "admin"},
        ]

        pwd_hash = hash_password("SecurePassword@123")
        for u in demo_users:
            canon = normalize_mobile(u["mobile"])
            existing = db.query(User).filter(User.mobile == canon).first()
            if not existing:
                user = User(
                    mobile=canon,
                    name=u["name"],
                    role=u["role"],
                    password_hash=pwd_hash,
                )
                db.add(user)
                print(f"[+] Created user: {u['name']} ({canon})")
            else:
                existing.password_hash = pwd_hash
                existing.role = u["role"]
                existing.name = u["name"]
                print(f"[*] Updated user: {u['name']} ({canon})")

            # Ensure synced to legacy tables
            if u["role"] == "farmer":
                f_exist = db.query(Farmer).filter(Farmer.name == u["name"]).first()
                if not f_exist:
                    db.add(Farmer(name=u["name"]))
            elif u["role"] == "buyer":
                b_exist = db.query(Buyer).filter(Buyer.name == u["name"]).first()
                if not b_exist:
                    db.add(Buyer(name=u["name"]))

        db.commit()
        print("Demo users seeded successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_users()

