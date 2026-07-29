#!/usr/bin/env python3
"""
Discord Server Cloner — Main entry point.

Usage:
    python main.py            # Launch the GUI
    python main.py --help     # Show help
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from gui.app import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
