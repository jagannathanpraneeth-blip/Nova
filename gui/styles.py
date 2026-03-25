DARK_THEME = """
QMainWindow {
    background-color: #0f0f1a;
}

QLabel {
    color: #00d9ff;
    font-family: 'Segoe UI', sans-serif;
}

QLabel#StatusLabel {
    font-size: 24px;
    font-weight: bold;
    color: #00d9ff;
}

QLabel#TranscriptLabel {
    font-size: 18px;
    color: #ffffff;
    padding: 10px;
}

QTextEdit {
    background-color: #1a1a2e;
    color: #00d9ff;
    border: 1px solid #00d9ff;
    border-radius: 5px;
    font-family: 'Consolas', monospace;
    font-size: 14px;
}

QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                      stop:0 #10283b, stop:1 #17324a);
    color: #9ef3ff;
    border: 1px solid #00d9ff;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #00d9ff;
    color: #0f0f1a;
}

QPushButton:pressed {
    background-color: #00b7d8;
    color: #071018;
}
"""
