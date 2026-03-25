from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout


class StatCard(QFrame):
    def __init__(self, title: str, value: str):
        super().__init__()
        self.setObjectName("DashboardCard")
        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("DashboardCardTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("DashboardCardValue")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def update_value(self, value: str):
        self.value_label.setText(value)


class MiniDashboard(QWidget):
    actionRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nova Dashboard")
        self.setMinimumSize(420, 300)
        self.setStyleSheet("""
            QWidget { background-color: #0f1726; color: #e8f6ff; }
            QFrame#DashboardCard {
                background: #132238;
                border: 1px solid #1c3755;
                border-radius: 14px;
                padding: 10px;
            }
            QLabel#DashboardTitle { font-size: 22px; font-weight: bold; color: #8be9fd; }
            QLabel#DashboardSubTitle { color: #89a7c2; font-size: 13px; }
            QLabel#DashboardCardTitle { color: #7fa5c3; font-size: 12px; }
            QLabel#DashboardCardValue { color: #ffffff; font-size: 24px; font-weight: bold; }
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

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("Nova Command Center")
        title.setObjectName("DashboardTitle")
        subtitle = QLabel("Quick actions, runtime snapshot, and future assistant controls.")
        subtitle.setObjectName("DashboardSubTitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.plugins_card = StatCard("Plugins", "Loaded")
        self.voice_card = StatCard("Voice", "Ready")
        self.ai_card = StatCard("LLM", "Online")
        stats_row.addWidget(self.plugins_card)
        stats_row.addWidget(self.voice_card)
        stats_row.addWidget(self.ai_card)
        root.addLayout(stats_row)

        for label, action in [
            ("Open Projects", "projects"),
            ("Open Social Tools", "social"),
            ("Open Settings", "settings"),
            ("Open Diagnostics", "diagnostics"),
            ("Hide Dashboard", "hide")
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, a=action: self.actionRequested.emit(a))
            root.addWidget(btn)

        root.addStretch()

    def update_runtime_state(self, voice: str = "Ready", llm: str = "Online", plugins: str = "Loaded"):
        self.voice_card.update_value(voice)
        self.ai_card.update_value(llm)
        self.plugins_card.update_value(plugins)
