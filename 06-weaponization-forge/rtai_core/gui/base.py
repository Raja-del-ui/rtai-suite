"""Base GUI helpers - shared worker thread."""
import subprocess
from pathlib import Path
try:
    from PySide6.QtCore import QThread, Signal
except ImportError:
    try:
        from PyQt6.QtCore import QThread, pyqtSignal as Signal
    except ImportError:
        QThread=object  # type: ignore
        Signal=lambda *a, **k: None  # type: ignore

class WorkerThread(QThread):  # type: ignore
    output_signal = Signal(str)
    finished_signal = Signal(int)
    error_signal = Signal(str)
    def __init__(self, command, cwd=None):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.process = None
    def run(self):
        try:
            self.process = subprocess.Popen(self.command, cwd=self.cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(self.process.stdout.readline, ''):
                if line: self.output_signal.emit(line.rstrip())
            self.process.wait()
            self.finished_signal.emit(self.process.returncode)
        except Exception as e:
            self.error_signal.emit(str(e))
    def stop(self):
        if self.process: self.process.terminate()
