"""
3D Model Generator AI Agent
A Python desktop application for converting images to 3D STL models
using TripoSR and Groq LLM.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("3D Model Generator AI Agent")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("3DModelGen")


    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

