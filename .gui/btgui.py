#!/usr/bin/env python
"""
BIOS Tool GUI - Graphical interface for bt build system
Provides workspace discovery, build management, and progress tracking
"""

import sys
import os

# Auto-install PyQt6 if not available
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
except ImportError:
    # PyQt6 not installed - install it automatically
    import ctypes
    import subprocess
    
    # Run pip install with visible console
    process = subprocess.Popen(
        [sys.executable, '-m', 'pip', 'install', 'PyQt6'],
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    process.wait()
    
    if process.returncode == 0:
        if sys.platform == 'win32':
            ctypes.windll.user32.MessageBoxW(0, 
                "PyQt6 installed successfully!\n\nPlease restart the BIOS Tool GUI.", 
                "Installation Complete", 
                0x40)  # MB_ICONINFORMATION
        else:
            print("PyQt6 installed successfully! Please restart the BIOS Tool GUI.")
    else:
        if sys.platform == 'win32':
            ctypes.windll.user32.MessageBoxW(0, 
                f"Failed to install PyQt6.\n\nTry running manually:\n{sys.executable} -m pip install PyQt6", 
                "Installation Failed", 
                0x10)  # MB_ICONERROR
        else:
            print(f"Failed to install PyQt6.\n\nTry running manually:\n{sys.executable} -m pip install PyQt6")
    sys.exit(1)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modular components
from ui import BTGui


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = BTGui()
    window.show()
    
    # Center the window after it's fully rendered
    def center_window():
        screen = app.primaryScreen().availableGeometry()
        window_rect = window.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        window.move(window_rect.topLeft())
    
    QTimer.singleShot(0, center_window)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
