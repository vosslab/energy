#!/usr/bin/env python3

import os
import runpy

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "apps", "wemoPlug-comed-old2.py")
runpy.run_path(SCRIPT_PATH, run_name="__main__")
