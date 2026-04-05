"""
Dark theme stylesheet for the 3D Model Generator AI Agent.
"""

DARK_THEME = """
/* ── Global ── */
QMainWindow, QDialog {
    background-color: #0f0f1a;
}
QWidget {
    background-color: #0f0f1a;
    color: #e2e2f0;
    font-family: "Helvetica Neue", "Arial", sans-serif;
    font-size: 13px;
}

/* ── Scroll bars ── */
QScrollBar:vertical {
    background: #1a1a2e;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #4a4a7a;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #6a6aba; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #1a1a2e;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #4a4a7a;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #6a6aba; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Panels / Frames ── */
QFrame#chatPanel, QFrame#workspacePanel {
    background-color: #13132a;
    border-radius: 12px;
    border: 1px solid #2a2a4a;
}

QFrame#headerFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a0533, stop:0.5 #0d1b4b, stop:1 #1a0533);
    border-bottom: 1px solid #3a2a7a;
}

QFrame#imageFrame {
    background-color: #1a1a2e;
    border: 2px dashed #3a3a6a;
    border-radius: 10px;
}
QFrame#imageFrame:hover {
    border-color: #7c6af7;
}

/* ── Chat display ── */
QTextBrowser#chatDisplay {
    background-color: #13132a;
    border: none;
    color: #e2e2f0;
    font-size: 13px;
    padding: 8px;
    border-radius: 8px;
    selection-background-color: #4a3a9a;
}

/* ── Input field ── */
QTextEdit#messageInput {
    background-color: #1e1e38;
    border: 1px solid #3a3a6a;
    border-radius: 10px;
    color: #e2e2f0;
    font-size: 13px;
    padding: 8px 12px;
}
QTextEdit#messageInput:focus {
    border: 1px solid #7c6af7;
}

QLineEdit {
    background-color: #1e1e38;
    border: 1px solid #3a3a6a;
    border-radius: 8px;
    color: #e2e2f0;
    font-size: 13px;
    padding: 6px 10px;
}
QLineEdit:focus {
    border: 1px solid #7c6af7;
}
QLineEdit[echoMode="2"] {
    lineedit-password-character: 9679;
}

/* ── Buttons ── */
QPushButton {
    background-color: #2a2a4a;
    color: #e2e2f0;
    border: 1px solid #4a4a7a;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #3a3a6a;
    border-color: #7c6af7;
}
QPushButton:pressed {
    background-color: #1a1a38;
}
QPushButton:disabled {
    background-color: #1a1a2e;
    color: #5a5a7a;
    border-color: #2a2a4a;
}

QPushButton#sendBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5a3af7, stop:1 #7c5af7);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 14px;
}
QPushButton#sendBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6a4af7, stop:1 #8c6af7);
}
QPushButton#sendBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a2af0, stop:1 #6a4af0);
}

QPushButton#uploadBtn {
    background-color: #1e3a5f;
    border-color: #2a5a8f;
    color: #7ab8f5;
}
QPushButton#uploadBtn:hover {
    background-color: #2a4a6f;
    border-color: #4a8abf;
}

QPushButton#convertBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a5a3a, stop:1 #2a7a4a);
    color: #7affc4;
    border: 1px solid #3a8a5a;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#convertBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2a6a4a, stop:1 #3a8a5a);
}
QPushButton#convertBtn:disabled {
    background-color: #1a2a1a;
    color: #3a5a3a;
    border-color: #2a3a2a;
}

QPushButton#downloadBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a2a1a, stop:1 #6a3a1a);
    color: #ffc77a;
    border: 1px solid #8a5a2a;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#downloadBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5a3a2a, stop:1 #7a4a2a);
}
QPushButton#downloadBtn:disabled {
    background-color: #2a1a0a;
    color: #5a3a1a;
    border-color: #3a2a1a;
}

QPushButton#clearBtn {
    background-color: transparent;
    border: 1px solid #4a3a5a;
    color: #9a7ab8;
    padding: 5px 12px;
    font-size: 12px;
}
QPushButton#clearBtn:hover {
    background-color: #2a1a3a;
    border-color: #7a5a9a;
}

/* ── Labels ── */
QLabel#titleLabel {
    color: #c8b8ff;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#subtitleLabel {
    color: #6a6a9a;
    font-size: 12px;
}
QLabel#sectionLabel {
    color: #9a9acc;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QLabel#statusLabel {
    color: #7affc4;
    font-size: 12px;
    padding: 4px 8px;
    background-color: #0a2a1a;
    border-radius: 6px;
    border: 1px solid #1a4a2a;
}
QLabel#imagePreviewLabel {
    color: #5a5a8a;
    font-size: 12px;
    qproperty-alignment: AlignCenter;
}

/* ── Progress bar ── */
QProgressBar {
    background-color: #1a1a2e;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5a3af7, stop:1 #3af77a);
    border-radius: 5px;
}

/* ── Combo box ── */
QComboBox {
    background-color: #1e1e38;
    border: 1px solid #3a3a6a;
    border-radius: 8px;
    color: #e2e2f0;
    padding: 5px 10px;
    font-size: 13px;
}
QComboBox:hover { border-color: #7c6af7; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #7c6af7;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e38;
    border: 1px solid #4a4a7a;
    color: #e2e2f0;
    selection-background-color: #4a3a9a;
    border-radius: 8px;
    padding: 4px;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #2a2a4a;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #7c6af7;
}

/* ── Status bar ── */
QStatusBar {
    background-color: #0a0a18;
    color: #6a6a9a;
    border-top: 1px solid #2a2a4a;
    font-size: 11px;
}

/* ── Dialog ── */
QDialog {
    background-color: #13132a;
}
QFormLayout QLabel {
    color: #9a9acc;
    font-size: 13px;
}

/* ── Tabs (if used) ── */
QTabWidget::pane {
    border: 1px solid #2a2a4a;
    background-color: #13132a;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #1a1a2e;
    color: #7a7aaa;
    padding: 8px 16px;
    border: none;
    font-size: 13px;
}
QTabBar::tab:selected {
    background-color: #2a2a4a;
    color: #c8b8ff;
    border-bottom: 2px solid #7c6af7;
}
QTabBar::tab:hover {
    background-color: #2a2a4a;
    color: #e2e2f0;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #2a2a4a;
    color: #e2e2f0;
    border: 1px solid #5a5a9a;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ── Message box ── */
QMessageBox {
    background-color: #13132a;
}
QMessageBox QLabel {
    color: #e2e2f0;
}
QMessageBox QPushButton {
    min-width: 80px;
}
"""


