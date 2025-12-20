#!/usr/bin/env python

import os
import runpy

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "plots", "plot_comed.py")
runpy.run_path(SCRIPT_PATH, run_name="__main__")
