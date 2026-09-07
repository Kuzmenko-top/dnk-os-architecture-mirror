# --- DNK-MRH-HEADER ---
# mrh_id: "conftest.py"
# purpose: "Test session-wide configuration, environment setup, and hook initialization for the DNK OS verification suite."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-13"
# --- END DNK-MRH-HEADER ---

import os
import sys

# Configure test environment variables before any test modules or application code is imported
os.environ["ENV"] = "test"
os.environ["APP_ENV"] = "test"
os.environ["NODE_ENV"] = "test"
