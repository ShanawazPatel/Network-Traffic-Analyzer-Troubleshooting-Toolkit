#!/usr/bin/env python3
"""Convenience launcher for the NetPulse Web SOC Dashboard."""
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from netpulse.visualizer.web_server import start_server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    start_server(host=host, port=port)
