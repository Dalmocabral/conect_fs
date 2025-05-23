import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QFont
from SimConnect import *
import time
import pygame

class SimConnectWorker(threading.Thread):
    def __init__(self, update_callback):
        super().__init__()
        self.update_callback = update_callback
        self.running = False

    def run(self):
        self.running = True 
        pygame.mixer.init()

        embarque_tocado = False
        boasvindas_tocado = False
        taxiamento_tocado = False
        tempo_embarque = None

        try:
            sm = SimConnect()
            self.update_callback("🟢 Conectado ao MSFS2020 com sucesso!")
            aircraft = AircraftRequests(sm, _time=2000)

            while self.running:
                try:
                    altitude = aircraft.get("PLANE_ALTITUDE") or 0
                    speed = aircraft.get("AIRSPEED_INDICATED") or 0
                    voltage = aircraft.get("ELECTRICAL_MAIN_BUS_VOLTAGE") or 0
                    ground_speed = aircraft.get("GROUND_VELOCITY") or 0
                    ground_speed_knots = ground_speed * 1.94384

                    # Áudio 1: Embarque (com try para detectar erro real)
                    if voltage > 1 and not embarque_tocado:
                        try:
                            pygame.mixer.music.load("audio/01_Embarque.mp3")
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Embarque")
                            embarque_tocado = True
                            tempo_embarque = time.time()
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de embarque: {e}")
                            embarque_tocado = False  # não marca como tocado se der erro

                    # Áudio 2: Boas Vindas (somente se embarque foi tocado com sucesso)
                    if embarque_tocado and not boasvindas_tocado:
                        if tempo_embarque and time.time() - tempo_embarque >= 90:
                            try:
                                pygame.mixer.music.load("audio/02_BoasVindas.mp3")
                                pygame.mixer.music.play()
                                self.update_callback("[✔️] Boas-vindas")
                                boasvindas_tocado = True
                            except Exception as e:
                                self.update_callback(f"⚠️ Erro ao tocar áudio de boas-vindas: {e}")

                    # Áudio 3: Taxiamento (somente se GROUND_SPEED > 5 knots)
                    if ground_speed_knots > 5 and not taxiamento_tocado:
                        try:
                            pygame.mixer.music.load("audio/03_Taxiamento.mp3")
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Taxiamento")
                            taxiamento_tocado = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de taxiamento: {e}")


                except Exception as e:
                    self.update_callback(f"⚠️ Erro ao ler dados da aeronave: {e}")
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
