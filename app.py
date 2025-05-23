import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QFont
from SimConnect import *
import time

class SimConnectWorker(threading.Thread):
    def __init__(self, update_callback):
        super().__init__()
        self.update_callback = update_callback
        self.running = False

    def run(self):
        self.running = True
        try:
            sm = SimConnect()
            self.update_callback("🟢 Conectado ao MSFS2020 com sucesso!")
            aircraft = AircraftRequests(sm, _time=2000)

            while self.running:
                try:
                    altitude = aircraft.get("PLANE_ALTITUDE")
                    speed = aircraft.get("AIRSPEED_INDICATED")
                    self.update_callback(f"🛫 ALT: {altitude:.2f} ft | SPEED: {speed:.2f} kt")
                except:
                    self.update_callback("⚠️ Erro ao ler dados da aeronave.")
                time.sleep(2)

        except ConnectionError:
            self.update_callback("🔴 Não foi possível conectar ao MSFS2020.")
        except Exception as e:
            self.update_callback(f"❌ Erro inesperado: {str(e)}")

    def stop(self):
        self.running = False

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSFS2020 - Áudio de Cabine")
        self.setFixedSize(500, 400)
        self.worker = None
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: #5A5A5A;")

        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setStyleSheet("background-color: black; color: white;")
        self.display.setFont(QFont("Consolas", 10))

        self.connect_btn = QPushButton("Conectar")
        self.stop_btn = QPushButton("Parar")
        self.connect_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.stop_btn.setFont(QFont("Arial", 12, QFont.Bold))

        style = """
            QPushButton {
                background-color: #8A8A8A;
                color: white;
                border: 1px solid black;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #AAAAAA;
            }
        """
        self.connect_btn.setStyleSheet(style)
        self.stop_btn.setStyleSheet(style)

        self.connect_btn.clicked.connect(self.start_connection)
        self.stop_btn.clicked.connect(self.stop_connection)

        layout = QVBoxLayout()
        layout.addWidget(self.display)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def start_connection(self):
        if not self.worker or not self.worker.is_alive():
            self.display.append("🔄 Tentando conectar...")
            self.worker = SimConnectWorker(self.update_display)
            self.worker.start()

    def stop_connection(self):
        if self.worker:
            self.worker.stop()
            self.display.append("⛔ Conexão encerrada.")
            self.worker = None

    def update_display(self, message):
        self.display.append(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
