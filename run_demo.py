#!/usr/bin/env python3
"""Convenience launcher for the NetPulse end-to-end interactive demo."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from netpulse.cli import cmd_demo

if __name__ == "__main__":
    class DemoArgs:
        pass
    cmd_demo(DemoArgs())
