#!/usr/bin/env python3
"""
Discord Server Cloner — Desktop GUI.

Usage:
    python main.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from gui.app import main
    main()
