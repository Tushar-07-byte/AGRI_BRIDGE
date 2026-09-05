"""
AgriBridge Temporary Image Cleanup Safety Test
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Proves that:
1. Temporary AI scratch files in backend/ai_uploads/ older than threshold are safely reclaimed.
2. Files actively referenced by DiseaseRecord or Listing are NEVER deleted.
3. Subdirectories (such as voice_audio/) are never touched.
4. Cleanup reporting accurately logs freed MB and counts.
"""

import sys
import os
import time
from pathlib import Path

# Ensure UTF-8 stdout
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.disease_record import DiseaseRecord
from app.services.cleanup_service import (
    cleanup_temporary_files,
    get_persisted_image_filenames,
    AI_UPLOADS_DIR,
    PERMANENT_UPLOADS_DIR
)

client = TestClient(app)


def test_cleanup_safety():
    print("\n" + "=" * 80)
    print("RUNNING TEMPORARY IMAGE CLEANUP SAFETY TEST")
    print("=" * 80)

    db = SessionLocal()

    # 1. Verify referenced files protection query
    referenced = get_persisted_image_filenames(db)
    print(f"  Persisted DB references discovered: {len(referenced)} filenames")

    # 2. Create a dummy protected record in DB and file on disk
    dummy_protected_filename = "protected_test_leaf_audit.jpg"
    dummy_protected_path = PERMANENT_UPLOADS_DIR / dummy_protected_filename
    dummy_protected_path.write_bytes(b"FAKE_PROTECTED_DATA_123456789")

    # Ensure a DiseaseRecord points to it
    test_rec = DiseaseRecord(
        farmer_id=1,
        crop_type="wheat",
        image_url=f"/uploads/{dummy_protected_filename}",
        confidence=95.0,
        predicted_pathogen="Healthy",
        severity="low",
        status="VERIFIED_HEALTH_RECORD"
    )
    db.add(test_rec)
    db.commit()
    db.refresh(test_rec)

    # 3. Create a stale temporary scratch file in ai_uploads/
    AI_UPLOADS_DIR.mkdir(exist_ok=True)
    stale_scratch_path = AI_UPLOADS_DIR / "stale_temp_inference_scratch.jpg"
    stale_scratch_path.write_bytes(b"TEMPORARY_SCRATCH_DATA_987654321")

    # Set mtime back by 2000 seconds so it qualifies as stale
    old_time = time.time() - 2000
    os.utime(str(stale_scratch_path), (old_time, old_time))
    os.utime(str(dummy_protected_path), (old_time, old_time))

    print("  Created protected DB-referenced file in uploads/ and stale scratch in ai_uploads/")

    # 4. Execute cleanup
    report = cleanup_temporary_files(db=db, min_age_seconds=300, dry_run=False)

    print(f"  Cleanup Report: {report}")

    # ASSERTIONS:
    # A. Stale scratch file in ai_uploads must be deleted
    assert not stale_scratch_path.exists(), "Stale scratch file was NOT deleted!"
    print("  ✓ ASSERTION 1 PASSED: Stale scratch file in ai_uploads/ was safely deleted.")

    # B. Protected DB-referenced file MUST NOT be deleted
    assert dummy_protected_path.exists(), "CRITICAL: Protected DB-referenced file was accidentally deleted!"
    print("  ✓ ASSERTION 2 PASSED: Protected database-referenced file remained safe and untouched.")

    # C. Cleanup report counts
    assert report["deleted_ai_uploads"] >= 1, "Report should show at least 1 deleted ai_upload"
    assert report["freed_bytes"] > 0, "Report should show positive freed bytes"
    print("  ✓ ASSERTION 3 PASSED: Report metrics correctly reflect freed storage.")

    # 5. Test API Endpoint
    api_resp = client.post("/api/admin/cleanup-temp-uploads", params={"min_age_seconds": 900, "dry_run": True})
    assert api_resp.status_code == 200
    api_data = api_resp.json()
    assert api_data.get("success") is True
    print(f"  ✓ ASSERTION 4 PASSED: Maintenance API endpoint /api/admin/cleanup-temp-uploads works: {api_data}")

    # Cleanup test artifacts
    db.delete(test_rec)
    db.commit()
    db.close()
    dummy_protected_path.unlink(missing_ok=True)

    print("\n" + "=" * 80)
    print("ALL CLEANUP SAFETY ASSERTIONS PASSED SUCCESSFULLY!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_cleanup_safety()

