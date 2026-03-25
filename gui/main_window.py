import sys
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient

from gui.styles import DARK_THEME
from modules.speech_engine import SpeechEngine
from modules.nlp_engine import NLPEngine
from modules.command_executor import CommandExecutor
from modules.tts_engine import TTSEngine
from modules.utils import load_json, DATA_DIR
from modules.ai_brain import AIBrain
from gui.dashboard import MiniDashboard
from gui.settings_dialog import SettingsDialog
from gui.diagnostics_dialog import DiagnosticsDialog
from config import APP_NAME, WAKE_WORD
import os

class AssistantThread(QThread):
    update_status = pyqtSignal(str)
    update_transcript = pyqtSignal(str)
    update_log = pyqtSignal(str)
    request_dashboard = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.tts = TTSEngine()
        self.speech = SpeechEngine()
        self.nlp = NLPEngine()
        self.executor = CommandExecutor(self.tts)
        self.ai_brain = AIBrain(self.tts, self.speech)  # NEW: Universal AI Brain with speech engine
        self.intents_data = load_json(os.path.join(DATA_DIR, 'intents.json'))

    def run(self):
        self.update_log.emit(f"{APP_NAME} initialized.")
        self.update_log.emit(f"Listening for wake word: '{WAKE_WORD}'.")
        self.tts.speak(f"Hello. I am {APP_NAME}. Systems are online and ready.")

        wake_word_primary = WAKE_WORD.lower()
        legacy_wake_word = "jarvis"

        while self.running:
            self.update_status.emit("Listening")
            text = self.speech.listen()
            
            if text:
                text_lower = text.lower()
                if wake_word_primary in text_lower or legacy_wake_word in text_lower:
                    self.update_log.emit("🎤 Wake word detected")
                    self.tts.speak("Yes?")
                    
                    command = text_lower.replace(wake_word_primary, "").replace(legacy_wake_word, "").strip()

                    if command:
                        self.update_status.emit("Processing")
                        self.update_transcript.emit(f"You: {APP_NAME}, {command}")
                        self.update_log.emit(f"Command: {command}")
                        
                        # Check for simple conversational intents first
                        intent, confidence = self.nlp.classify_intent(command)
                        self.update_log.emit(f"Intent: {intent} ({confidence:.2f})")
                        
                        # PRIORITY CHANGE: Try AI Brain FIRST for everything
                        # This ensures commands like "type this" aren't mistaken for "identity"
                        self.update_log.emit("AI Brain processing command...")
                        result = self.ai_brain.parse_and_execute(command)
                        
                        if result['success'] and result['action'] != 'none':
                            # AI Brain handled it successfully
                            self.update_log.emit(f"✓ {result['action']}: {result['message']}")
                            if result['message']:
                                self.update_transcript.emit(f"Nova: {result['message']}")
                                
                            # Handle GUI-specific actions
                            if result['action'] == 'open_dashboard':
                                self.request_dashboard.emit(True)
                            elif result['action'] == 'close_dashboard':
                                self.request_dashboard.emit(False)
                        else:
                            # AI Brain didn't handle it, try conversational intents
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
                else:
                    # Intentionally silent on non-wake chatter to reduce log spam
                    pass
            
            time.sleep(0.5)

    def stop(self):
        self.running = False

class PulsingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.radius = 60
        self.ring_rotation = 0
        self.growing = True
        self.base_color = QColor(0, 255, 255) # Cyan
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
        
        # 1. Outer Glow
        gradient = QRadialGradient(center_x, center_y, 100)
        gradient.setColorAt(0, QColor(0, 255, 255, 100))
        gradient.setColorAt(1, QColor(0, 255, 255, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), 100, 100)

        # 2. Tech Ring (Rotating)
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.ring_rotation)
        pen = QPen(self.base_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw segmented ring
        for i in range(0, 360, 45):
             painter.drawArc(-80, -80, 160, 160, i * 16, 30 * 16)
             
        painter.restore()
        
        # 3. Inner Core (Pulsing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(self.radius), int(self.radius))
        
        # 4. Center Dot
        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), 20, 20)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Desktop AI Assistant")

        self.setGeometry(100, 100, 900, 680)
        self.setStyleSheet(DARK_THEME)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
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
        layout.addLayout(header_layout)
        
        self.pulsing_widget = PulsingWidget()
        layout.addWidget(self.pulsing_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.transcript_label = QLabel(f"Say '{WAKE_WORD}' to activate...")
        self.transcript_label.setObjectName("TranscriptLabel")
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.transcript_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(220)
        self.log_output.setPlaceholderText(f"{APP_NAME} runtime log...")
        layout.addWidget(self.log_output)
        
        self.thread = None
        self.dashboard = MiniDashboard()
        self.dashboard.actionRequested.connect(self.handle_dashboard_action)
        self.settings_dialog = None
        self.diagnostics_dialog = None
        
        QTimer.singleShot(500, self.start_assistant)

    def start_assistant(self):
        if self.thread and self.thread.isRunning():
            self.append_log("Assistant is already running.")
            return

        self.status_label.setText("Starting...")
        self.thread = AssistantThread()
        self.thread.update_status.connect(self.update_status)
        self.thread.update_transcript.connect(self.update_transcript)
        self.thread.update_log.connect(self.append_log)
        self.thread.request_dashboard.connect(self.toggle_dashboard)
        self.thread.finished.connect(lambda: self.status_label.setText("Stopped"))
        self.thread.start()
        self.append_log(f"{APP_NAME} started.")

    def stop_assistant(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait(3000)
            self.append_log(f"{APP_NAME} stopped.")
        self.status_label.setText("Stopped")

    def update_status(self, text):
        self.status_label.setText(text)

    def update_transcript(self, text):
        self.transcript_label.setText(text)

    def append_log(self, text):
        self.log_output.append(text)
        # Scroll to bottom
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())
        
    def toggle_dashboard(self, show):
        if show:
            self.dashboard.show()
        else:
            self.dashboard.hide()

    def collect_diagnostics_text(self):
        plugin_count = len(getattr(self.thread, 'plugin_manager', {}).plugins) if self.thread and hasattr(self.thread, 'plugin_manager') else 'unknown'
        runtime_lines = [
            f'App Name: {APP_NAME}',
            f'Wake Word: {WAKE_WORD}',
            f'Assistant Running: {bool(self.thread and self.thread.isRunning())}',
            f'Dashboard Visible: {self.dashboard.isVisible()}',
            f'Plugin Count: {plugin_count}',
            f'Current Status Label: {self.status_label.text()}',
        ]
        return '\n'.join(map(str, runtime_lines))

    def closeEvent(self, event):
        self.stop_assistant()
        event.accept()
