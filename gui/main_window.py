import sys
import threading
import time
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient

from gui.styles import DARK_THEME
from modules.speech_engine import SpeechEngine
from modules.nlp_engine import NLPEngine
from modules.command_executor import CommandExecutor
from modules.tts_engine import TTSEngine
from modules.utils import load_json, DATA_DIR
from modules.agents.orchestrator import Orchestrator
from modules.agents.autonomous_loop import AutonomousLoop
from gui.dashboard import MiniDashboard
from gui.settings_dialog import SettingsDialog
from gui.diagnostics_dialog import DiagnosticsDialog
from config import APP_NAME, WAKE_WORD, AUTONOMOUS_MODE


class AssistantThread(QThread):
    update_status = pyqtSignal(str)
    update_transcript = pyqtSignal(str)
    update_log = pyqtSignal(str)
    request_dashboard = pyqtSignal(bool)
    agents_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.tts = TTSEngine()
        self.speech = SpeechEngine()
        self.nlp = NLPEngine()
        self.executor = CommandExecutor(self.tts)
        
        # Initialize Multi-Agent Orchestrator
        self.orchestrator = Orchestrator(self.tts, self.speech)
        self.intents_data = load_json(os.path.join(DATA_DIR, 'intents.json'))
        
        # Background Autonomous supervisor loop
        self.auto_loop = None
        if AUTONOMOUS_MODE:
            self.auto_loop = AutonomousLoop(self.tts, self.orchestrator)
            self.auto_loop.start()

    def run(self):
        self.update_log.emit(f"{APP_NAME} initialized.")
        self.update_log.emit("Autonomous Agent Registry online.")
        self.update_log.emit(f"Listening for wake word: '{WAKE_WORD}'.")
        self.tts.speak(f"Hello. I am {APP_NAME}. Multiagent systems are online and running autonomously.")

        wake_word_primary = WAKE_WORD.lower()
        legacy_wake_word = "jarvis"

        while self.running:
            self.update_status.emit("Listening")
            
            # Emit agent statuses to update GUI list
            self.agents_updated.emit(self.orchestrator.get_agent_status())
            
            text = self.speech.listen()
            
            if text:
                text_lower = text.lower()
                if wake_word_primary in text_lower or legacy_wake_word in text_lower:
                    self.update_log.emit("🎤 Wake word heard")
                    self.tts.speak("Yes?")
                    
                    command = text_lower.replace(wake_word_primary, "").replace(legacy_wake_word, "").strip()

                    if command:
                        self.update_status.emit("Processing")
                        self.update_transcript.emit(f"You: {APP_NAME}, {command}")
                        self.update_log.emit(f"Command: {command}")
                        
                        # Check for simple conversational intents first
                        intent, confidence = self.nlp.classify_intent(command)
                        self.update_log.emit(f"Intent Classify: {intent} ({confidence:.2f})")
                        
                        # Orchestrator handles multi-agent task execution
                        self.update_log.emit("Orchestrator decomposing task...")
                        result = self.orchestrator.process(command)
                        
                        # Emit agent updates after work
                        self.agents_updated.emit(self.orchestrator.get_agent_status())
                        
                        if result['success'] and result['action'] != 'none':
                            self.update_log.emit(f"✓ {result['action']}: {result['message']}")
                            if result['message']:
                                self.update_transcript.emit(f"Nova: {result['message']}")
                                
                            if result['action'] == 'open_dashboard':
                                self.request_dashboard.emit(True)
                            elif result['action'] == 'close_dashboard':
                                self.request_dashboard.emit(False)
                        else:
                            # Conversational fallbacks
                            response_found = False
                            if intent in ["greeting", "goodbye", "thanks", "identity"]:
                                for i in self.intents_data['intents']:
                                    if i['tag'] == intent:
                                        import random
                                        resp = random.choice(i['responses'])
                                        resp = resp.replace('Jarvis', APP_NAME).replace('J.A.R.V.I.S.', APP_NAME)
                                        self.tts.speak(resp)
                                        self.update_transcript.emit(f"{APP_NAME}: {resp}")
                                        response_found = True
                                        if intent == "goodbye":
                                            self.running = False
                                            time.sleep(1)
                                            QApplication.quit()
                                        break
                            
                            if not response_found:
                                if intent != "unknown":
                                    entities = self.nlp.extract_entities(command)
                                    fallback_result = self.executor.execute(intent, command, entities)
                                    if fallback_result:
                                        self.update_transcript.emit(f"{APP_NAME}: {fallback_result}")
                                else:
                                    self.update_log.emit(f"✗ {result['action']}: {result['message']}")
                    else:
                        self.update_log.emit("Wake word heard. Waiting for command...")
            
            time.sleep(0.5)

    def stop(self):
        self.running = False
        if self.auto_loop:
            self.auto_loop.stop()
        self.orchestrator.shutdown()


class PulsingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.radius = 60
        self.ring_rotation = 0
        self.growing = True
        self.base_color = QColor(0, 255, 255)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        
    def animate(self):
        if self.growing:
            self.radius += 0.5
            if self.radius >= 70:
                self.growing = False
        else:
            self.radius -= 0.5
            if self.radius <= 60:
                self.growing = True
        
        self.ring_rotation = (self.ring_rotation + 2) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Glow
        gradient = QRadialGradient(center_x, center_y, 100)
        gradient.setColorAt(0, QColor(0, 255, 255, 100))
        gradient.setColorAt(1, QColor(0, 255, 255, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), 100, 100)

        # Tech Ring
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.ring_rotation)
        pen = QPen(self.base_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        for i in range(0, 360, 45):
             painter.drawArc(-80, -80, 160, 160, i * 16, 30 * 16)
        painter.restore()
        
        # Inner Core
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(self.radius), int(self.radius))
        
        # Core center
        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), 20, 20)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Advanced Autonomous Multiagent System")
        self.setGeometry(100, 100, 1100, 720)
        self.setStyleSheet(DARK_THEME)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main split layout (Left = controls/log, Right = agent registry swarm)
        main_layout = QHBoxLayout(central_widget)
        left_panel = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("StatusLabel")
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()
        self.start_button = QPushButton("Start Listening")
        self.start_button.clicked.connect(self.start_assistant)
        self.stop_button = QPushButton("Stop Listening")
        self.stop_button.clicked.connect(self.stop_assistant)
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(lambda: self.log_output.clear())
        header_layout.addWidget(self.start_button)
        header_layout.addWidget(self.stop_button)
        header_layout.addWidget(self.clear_button)
        left_panel.addLayout(header_layout)
        
        self.pulsing_widget = PulsingWidget()
        left_panel.addWidget(self.pulsing_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.transcript_label = QLabel(f"Say '{WAKE_WORD}' to activate...")
        self.transcript_label.setObjectName("TranscriptLabel")
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(self.transcript_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(260)
        self.log_output.setPlaceholderText(f"{APP_NAME} runtime swarm log...")
        left_panel.addWidget(self.log_output)
        
        main_layout.addLayout(left_panel, stretch=2)
        
        # Right Panel: Agent Swarm List Widget
        right_panel = QVBoxLayout()
        agent_title = QLabel("Agent Swarm Registry")
        agent_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #8be9fd;")
        right_panel.addWidget(agent_title)
        
        self.agent_table = QTableWidget()
        self.agent_table.setColumnCount(3)
        self.agent_table.setHorizontalHeaderLabels(["Agent", "State", "Capabilities"])
        self.agent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.agent_table.setStyleSheet("""
            QTableWidget {
                background-color: #111125;
                color: #e8f6ff;
                border: 1px solid #1c3755;
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
            }
            QHeaderView::section {
                background-color: #1a1a36;
                color: #8be9fd;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #1c3755;
            }
        """)
        right_panel.addWidget(self.agent_table)
        
        main_layout.addLayout(right_panel, stretch=1)
        
        self.thread = None
        self.dashboard = MiniDashboard()
        self.dashboard.actionRequested.connect(self.handle_dashboard_action)
        self.settings_dialog = None
        self.diagnostics_dialog = None
        
        QTimer.singleShot(500, self.start_assistant)

    def start_assistant(self):
        if self.thread and self.thread.isRunning():
            self.append_log("Assistant swarm is already running.")
            return

        self.status_label.setText("Starting Swarm...")
        self.thread = AssistantThread()
        self.thread.update_status.connect(self.update_status)
        self.thread.update_transcript.connect(self.update_transcript)
        self.thread.update_log.connect(self.append_log)
        self.thread.request_dashboard.connect(self.toggle_dashboard)
        self.thread.agents_updated.connect(self.update_agent_table)
        self.thread.finished.connect(lambda: self.status_label.setText("Stopped"))
        self.thread.start()
        self.append_log(f"{APP_NAME} multiagent swarm started.")

    def stop_assistant(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait(3000)
            self.append_log(f"{APP_NAME} multiagent swarm stopped.")
        self.status_label.setText("Stopped")

    def update_status(self, text):
        self.status_label.setText(text)

    def update_transcript(self, text):
        self.transcript_label.setText(text)

    def append_log(self, text):
        self.log_output.append(text)
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_agent_table(self, agent_status_list):
        self.agent_table.setRowCount(len(agent_status_list))
        for row, agent in enumerate(agent_status_list):
            # Name
            self.agent_table.setItem(row, 0, QTableWidgetItem(agent["name"]))
            # State
            state_item = QTableWidgetItem(agent["state"])
            if agent["state"] == "busy":
                state_item.setForeground(QColor(255, 184, 108)) # Orange
            elif agent["state"] == "error":
                state_item.setForeground(QColor(255, 85, 85)) # Red
            else:
                state_item.setForeground(QColor(80, 250, 123)) # Green
            self.agent_table.setItem(row, 1, state_item)
            # Capabilities
            self.agent_table.setItem(row, 2, QTableWidgetItem(", ".join(agent["capabilities"])))
        
    def toggle_dashboard(self, show):
        if show:
            self.dashboard.show()
        else:
            self.dashboard.hide()

    def handle_dashboard_action(self, action):
        self.append_log(f"Dashboard action requested: {action}")
        if action == "hide":
            self.dashboard.hide()
        elif action == "settings":
            if not self.settings_dialog:
                self.settings_dialog = SettingsDialog(self)
            self.settings_dialog.show()
        elif action == "diagnostics":
            if not self.diagnostics_dialog:
                self.diagnostics_dialog = DiagnosticsDialog(self)
            self.diagnostics_dialog.set_runtime_data(self.collect_diagnostics_text())
            self.diagnostics_dialog.show()
        elif action == "projects":
            self.append_log("Invoking CodingAgent for project panel management.")
        elif action == "social":
            self.append_log("Invoking CommunicationAgent for social dashboard.")

    def collect_diagnostics_text(self):
        agent_count = self.thread.orchestrator.get_agent_count() if self.thread else 'unknown'
        runtime_lines = [
            f'App Name: {APP_NAME}',
            f'Wake Word: {WAKE_WORD}',
            f'Autonomous Loop Enabled: {AUTONOMOUS_MODE}',
            f'Agent Count: {agent_count}',
            f'Dashboard Visible: {self.dashboard.isVisible()}',
            f'Current Status Label: {self.status_label.text()}',
        ]
        return '\n'.join(map(str, runtime_lines))

    def closeEvent(self, event):
        self.stop_assistant()
        event.accept()
