import json
import os
import sys
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets
import subprocess

APP_NAME = "QuizReminder"
CONFIG_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "settings.json"


def is_dark_mode():
    """Return True if macOS dark mode is active."""
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


class ConfigWindow(QtWidgets.QWidget):
    start_timer = QtCore.pyqtSignal(int, str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz Reminder Settings")
        self.setWindowIcon(QtGui.QIcon("icon.icns"))
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        form_layout = QtWidgets.QFormLayout()
        self.question_edit = QtWidgets.QTextEdit()
        self.answer_edit = QtWidgets.QLineEdit()
        self.timer_spin = QtWidgets.QSpinBox()
        self.timer_spin.setRange(1, 3600)
        self.timer_spin.setSuffix(" s")

        form_layout.addRow("Question", self.question_edit)
        form_layout.addRow("Answer", self.answer_edit)
        form_layout.addRow("Timer", self.timer_spin)
        layout.addLayout(form_layout)

        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start")
        self.reset_btn = QtWidgets.QPushButton("Reset")
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.start_btn.clicked.connect(self.start_clicked)
        self.reset_btn.clicked.connect(self.reset_fields)

    def start_clicked(self):
        question = self.question_edit.toPlainText()
        answer = self.answer_edit.text()
        seconds = int(self.timer_spin.value())
        self.save_settings()
        self.start_timer.emit(seconds, question, answer)

    def reset_fields(self):
        self.question_edit.clear()
        self.answer_edit.clear()
        self.timer_spin.setValue(1)

    def load_settings(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                self.question_edit.setPlainText(data.get("question", ""))
                self.answer_edit.setText(data.get("answer", ""))
                self.timer_spin.setValue(data.get("timer", 1))
            except Exception:
                pass

    def save_settings(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "question": self.question_edit.toPlainText(),
            "answer": self.answer_edit.text(),
            "timer": int(self.timer_spin.value()),
        }
        CONFIG_FILE.write_text(json.dumps(data))


class QuizWindow(QtWidgets.QWidget):
    answer_submitted = QtCore.pyqtSignal(str)

    def __init__(self, question):
        super().__init__()
        self.setWindowTitle("Quiz")
        self.setWindowIcon(QtGui.QIcon("icon.icns"))
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        layout = QtWidgets.QVBoxLayout()
        self.question_label = QtWidgets.QLabel(question)
        self.answer_edit = QtWidgets.QLineEdit()
        self.submit_btn = QtWidgets.QPushButton("Submit")
        layout.addWidget(self.question_label)
        layout.addWidget(self.answer_edit)
        layout.addWidget(self.submit_btn)
        self.setLayout(layout)
        self.submit_btn.clicked.connect(self.submit)

    def submit(self):
        self.answer_submitted.emit(self.answer_edit.text())
        self.close()


class ResultWindow(QtWidgets.QWidget):
    config_again = QtCore.pyqtSignal()

    def __init__(self, user_answer, correct_answer):
        super().__init__()
        self.setWindowTitle("Result")
        self.setWindowIcon(QtGui.QIcon("icon.icns"))
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel(f"Your answer: {user_answer}"))
        layout.addWidget(QtWidgets.QLabel(f"Correct answer: {correct_answer}"))
        self.again_btn = QtWidgets.QPushButton("Configure Again")
        layout.addWidget(self.again_btn)
        self.setLayout(layout)
        self.again_btn.clicked.connect(self.config_again.emit)


class TrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.menu = QtWidgets.QMenu()
        self.open_action = self.menu.addAction("Open Settings")
        self.toggle_action = self.menu.addAction("Start Timer")
        self.menu.addSeparator()
        quit_action = self.menu.addAction("Quit")
        self.setContextMenu(self.menu)
        self.open_action.triggered.connect(parent.show)
        quit_action.triggered.connect(QtWidgets.qApp.quit)
        self.toggle_action.triggered.connect(parent.toggle_timer)

    def update_toggle(self, running):
        self.toggle_action.setText("Stop Timer" if running else "Start Timer")


class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.tray = TrayIcon(QtGui.QIcon("icon.icns"), self)
        self.tray.show()
        self.config_window = ConfigWindow()
        self.config_window.start_timer.connect(self.start_timer)
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timer_finished)
        self.question = ""
        self.correct_answer = ""
        self.quiz_window = None

    def show(self):
        self.config_window.show()
        self.config_window.raise_()
        self.config_window.activateWindow()

    def toggle_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.tray.update_toggle(False)
            self.tray.showMessage(APP_NAME, "Timer stopped")
        else:
            self.config_window.start_clicked()

    def start_timer(self, seconds, question, answer):
        self.question = question
        self.correct_answer = answer
        self.timer.start(seconds * 1000)
        self.tray.update_toggle(True)
        self.tray.showMessage(APP_NAME, f"Timer started ({seconds}s)")
        self.config_window.hide()

    def timer_finished(self):
        try:
            from pync import Notifier
            Notifier.notify("Time is up!", title=APP_NAME, activate=APP_NAME)
        except Exception:
            self.tray.showMessage(APP_NAME, "Time is up!")

        self.quiz_window = QuizWindow(self.question)
        self.quiz_window.answer_submitted.connect(self.show_result)
        self.quiz_window.show()
        self.tray.update_toggle(False)

    def show_result(self, user_answer):
        result = ResultWindow(user_answer, self.correct_answer)
        result.config_again.connect(self.show)
        result.show()
        self.quiz_window = None


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    if is_dark_mode():
        app.setStyle("Fusion")
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        app.setPalette(palette)
    qt_app = App()
    qt_app.show()
    sys.exit(app.exec_())
