"""
Shared Test Utilities & Path Resolvers for AgriBridge Test Suite
"""

import os
import sys
from pathlib import Path

# Workspace & Directory Definitions
TESTS_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = TESTS_DIR.parent
BACKEND_DIR = WORKSPACE_DIR / "backend"
FRONTEND_DIR = WORKSPACE_DIR / "frontend"
AI_ENGINE_DIR = WORKSPACE_DIR / "ai_engine"
FIXTURES_DIR = TESTS_DIR / "fixtures"
TEST_IMAGES_DIR = FIXTURES_DIR / "test_images" if (FIXTURES_DIR / "test_images").exists() else BACKEND_DIR / "test_images"

# Ensure backend and ai_engine are in sys.path
for p in [str(BACKEND_DIR), str(AI_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

def get_test_image(filename: str) -> str:
    """Returns absolute path to a test image fixture."""
    candidates = [
        TEST_IMAGES_DIR / filename,
        FIXTURES_DIR / "test_images" / filename,
        BACKEND_DIR / "test_images" / filename,
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(TEST_IMAGES_DIR / filename)
