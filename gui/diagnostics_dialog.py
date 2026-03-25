from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
from pathlib import Path
from config import APP_NAME


class DiagnosticsDialog(QDialog):
    def __init__(self, diagnostics_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} Diagnostics")
        self.setMinimumSize(640, 460)
        self.setStyleSheet("""
            QDialog { background-color: #0f1726; color: #e8f6ff; }
            QLabel#Title { font-size: 22px; font-weight: bold; color: #8be9fd; }
            QLabel#Muted { color: #89a7c2; font-size: 13px; }
            QTextEdit {
                background: #132238;
                border: 1px solid #1c3755;
                border-radius: 14px;
                padding: 12px;
                color: #e8f6ff;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QPushButton {
                background-color: #16314d;
                color: #9ef3ff;
                border: 1px solid #00d9ff;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #00d9ff; color: #071018; }
        """)

        layout = QVBoxLayout(self)
        title = QLabel("Diagnostics")
        title.setObjectName("Title")
        subtitle = QLabel("Use this to understand runtime state quickly instead of digging through logs blindly.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("Muted")

        body = QTextEdit()
        body.setReadOnly(True)
        body.setPlainText(diagnostics_text or "No diagnostics collected yet.")

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(body)
        layout.addWidget(close_btn)
