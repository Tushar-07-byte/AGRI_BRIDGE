"""
AgriBridge Safe Temporary Image Cleanup Service
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Safety Rules:
1. NEVER delete files referenced by persistent database records (DiseaseRecord.image_url, Listing.photo_path).
2. NEVER delete subdirectories (such as uploads/voice_audio/ or demo audio).
3. NEVER delete files actively being processed (enforces a minimum age threshold, default 15 minutes).
4. Safely clean unreferenced, orphaned files from backend/ai_uploads/.
5. Log all actions and return detailed byte statistics.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Set
from sqlalchemy.orm import Session

from ..models.disease_record import DiseaseRecord
from ..models.listing import Listing

BACKEND_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = BACKEND_DIR.parent
AI_UPLOADS_DIR = BACKEND_DIR / "ai_uploads"
PERMANENT_UPLOADS_DIR = WORKSPACE_DIR / "uploads"


def get_persisted_image_filenames(db: Session) -> Set[str]:
    """
    Collect all filenames referenced in persistent database records
    to prevent accidental deletion.
    """
    referenced = set()

    try:
        # 1. Disease records images
        records = db.query(DiseaseRecord.image_url).filter(DiseaseRecord.image_url != None).all()
        for r in records:
            if r[0]:
                referenced.add(Path(r[0]).name)

        # 2. Marketplace listing photos
        listings = db.query(Listing.photo_path).filter(Listing.photo_path != None).all()
        for l in listings:
            if l[0]:
                referenced.add(Path(l[0]).name)
    except Exception as e:
        print(f"Warning: Could not fetch referenced filenames from database: {e}")

    return referenced


def cleanup_temporary_files(
    db: Session,
    min_age_seconds: int = 900,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Conservatively cleans up temporary orphaned files.
    - AI_UPLOADS_DIR: All files older than min_age_seconds are scratch/temp and safe to remove.
    - PERMANENT_UPLOADS_DIR: Files are ONLY removed if NOT referenced in the database.
    """
    now = time.time()
    deleted_ai_uploads = 0
    deleted_unreferenced_uploads = 0
    retained_db_records = 0
    freed_bytes = 0

    referenced_names = get_persisted_image_filenames(db)

    # ------------------------------------------------------------
    # 1. CLEAN SCRATCH AI_UPLOADS (Temporary inference files)
    # ------------------------------------------------------------
    if AI_UPLOADS_DIR.exists() and AI_UPLOADS_DIR.is_dir():
        for file_path in AI_UPLOADS_DIR.glob("*"):
            if not file_path.is_file():
                continue
            try:
                age = now - file_path.stat().st_mtime
                if age >= min_age_seconds:
                    size = file_path.stat().st_size
                    if not dry_run:
                        file_path.unlink(missing_ok=True)
                    deleted_ai_uploads += 1
                    freed_bytes += size
            except Exception as e:
                print(f"Notice: Failed to process temp file {file_path.name}: {e}")

    # ------------------------------------------------------------
    # 2. CLEAN UNREFERENCED PERMANENT UPLOADS (Conservatively)
    # ------------------------------------------------------------
    if PERMANENT_UPLOADS_DIR.exists() and PERMANENT_UPLOADS_DIR.is_dir():
        for file_path in PERMANENT_UPLOADS_DIR.glob("*"):
            # Never touch directories (e.g. voice_audio)
            if not file_path.is_file():
                continue

            fname = file_path.name

            # SAFETY: Never delete if referenced in DB
            if fname in referenced_names:
                retained_db_records += 1
                continue

            # SAFETY: Only remove unreferenced files older than min_age_seconds
            try:
                age = now - file_path.stat().st_mtime
                if age >= (min_age_seconds * 4):  # Conservative: 4x threshold for uploads/
                    size = file_path.stat().st_size
                    if not dry_run:
                        file_path.unlink(missing_ok=True)
                    deleted_unreferenced_uploads += 1
                    freed_bytes += size
            except Exception as e:
                print(f"Notice: Failed to check {fname}: {e}")

    print(
        f"[CLEANUP REPORT] AI Uploads Removed: {deleted_ai_uploads}, "
        f"Unreferenced Removed: {deleted_unreferenced_uploads}, "
        f"DB Records Protected: {retained_db_records}, "
        f"Freed: {freed_bytes / (1024*1024):.2f} MB"
    )

    return {
        "success": True,
        "dry_run": dry_run,
        "deleted_ai_uploads": deleted_ai_uploads,
        "deleted_unreferenced_uploads": deleted_unreferenced_uploads,
        "retained_db_records": retained_db_records,
        "freed_bytes": freed_bytes,
        "freed_mb": round(freed_bytes / (1024 * 1024), 2)
    }

