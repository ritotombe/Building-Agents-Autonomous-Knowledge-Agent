from pathlib import Path

# This file lives at solution/agentic/tools/db_paths.py
# Parents[2] => solution/ (the solution package root)
SOLUTION_ROOT = Path(__file__).resolve().parents[2]

CULTPASS_DB = SOLUTION_ROOT / "data" / "external" / "cultpass.db"
UDAHUB_DB = SOLUTION_ROOT / "data" / "core" / "udahub.db"
