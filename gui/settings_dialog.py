from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
from config import APP_NAME, WAKE_WORD, OPENAI_API_KEY, GEMINI_API_KEY, NEWSAPI_KEY


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setMinimumSize(560, 420)
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
        title = QLabel("Settings & Environment")
        title.setObjectName("Title")
        subtitle = QLabel("Nova now prefers environment-based configuration. Put secrets in .env rather than hardcoding them into project files.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("Muted")

        body = QTextEdit()
        body.setReadOnly(True)
        body.setPlainText(
            f"APP_NAME={APP_NAME}\n"
            f"WAKE_WORD={WAKE_WORD}\n"
            f"OPENAI_API_KEY={'SET' if OPENAI_API_KEY else 'NOT SET'}\n"
            f"GEMINI_API_KEY={'SET' if GEMINI_API_KEY else 'NOT SET'}\n"
            f"NEWSAPI_KEY={'SET' if NEWSAPI_KEY else 'NOT SET'}\n\n"
            "Recommended next step:\n"
            "1. Copy .env.example to .env\n"
            "2. Add only the keys you really use\n"
            "3. Keep data/config.json free of secrets\n"
        )

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(body)
        layout.addWidget(close_btn)
