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
        seguranca_tocado = False
        preparacao_tocada = False
        audio10000_tocado = False
        cruzeiro_tocado = False
        ultima_altitude = None
        descida_tocada = False
        ultima_altitude = None
        pouso_tocado = False
        tempo_no_solo = None
        on_ground_anterior = False
        tempo_nivelado = 0


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
                    strobe_on = aircraft.get("LIGHT_STROBE_ON") or 0
                    altitude = aircraft.get("PLANE_ALTITUDE") or 0
                    vertical_speed = aircraft.get("VERTICAL_SPEED") or 0
                    on_ground = aircraft.get("SIM_ON_GROUND")
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

                    # Áudio 3: Segurança (quando velocidade no solo > 5)
                    if ground_speed_knots > 3 and not seguranca_tocado:
                        try:
                            pygame.mixer.music.load("audio/03_Seguranca.mp3")  # renomeado
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Áudio de segurança")
                            seguranca_tocado = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de segurança: {e}")

                    # Áudio 4: Taxiamento (quando ground speed > 10, mas só uma vez)
                    if ground_speed_knots > 10 and not taxiamento_tocado:
                        try:
                            pygame.mixer.music.load("audio/04_Taxiamento.mp3")
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Taxiamento iniciado")
                            taxiamento_tocado = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de taxiamento: {e}")

                    # Áudio 5: Preparação para decolagem (quando strobe ON)
                    if strobe_on == 1 and not preparacao_tocada:
                        try:
                            pygame.mixer.music.load("audio/05_PreparemTripulacao.mp3")
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Preparação para decolagem")
                            preparacao_tocada = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de preparação: {e}")

                    # Áudio 6: Passagem de 10.000 pés
                    if altitude > 10000 and not audio10000_tocado:
                        try:
                            pygame.mixer.music.load("audio/06_10000Pes.mp3")
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Acima de 10.000 pés")
                            audio10000_tocado = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de 10.000 pés: {e}")

                    # Condições para áudio de cruzeiro
                    if altitude > 13000:
                        if ultima_altitude is not None and abs(altitude - ultima_altitude) < 30:
                            tempo_nivelado += 2  # 2 segundos por iteração do loop
                        else:
                            tempo_nivelado = 0

                        ultima_altitude = altitude

                        vertical_speed = aircraft.get("VERTICAL_SPEED") or 0

                        if (abs(vertical_speed) < 100) and (tempo_nivelado >= 120) and not cruzeiro_tocado:
                            try:
                                pygame.mixer.music.load("audio/07_Cruzeiro.mp3")
                                pygame.mixer.music.play()
                                self.update_callback("[✔️] Cruzeiro alcançado")
                                cruzeiro_tocado = True
                            except Exception as e:
                                self.update_callback(f"⚠️ Erro ao tocar áudio de cruzeiro: {e}")

                    # Detecta início da descida real
                    if (
                        not descida_tocada
                        and cruzeiro_tocado  # evita conflito com fase de subida
                        and altitude < 10000
                        and vertical_speed < -1300
                        and ultima_altitude is not None
                        and ultima_altitude > 10000
                    ):
                        try:
                            pygame.mixer.music.load("audio/08_Descida.mp3")
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Descida iniciada")
                            descida_tocada = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de descida: {e}")

                    ultima_altitude = altitude

                    # Detectar toque no solo
                    if (
                        on_ground and not on_ground_anterior
                        and ground_speed_knots > 30
                        and not pouso_tocado
                    ):
                        tempo_no_solo = time.time()

                    # Se está no solo há mais de 15 segundos e ainda não tocou o áudio
                    if (
                        on_ground and tempo_no_solo
                        and time.time() - tempo_no_solo >= 15
                        and not pouso_tocado
                    ):
                        try:
                            pygame.mixer.music.load("audio/09_Pouso.mp3")
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Pouso confirmado")
                            pouso_tocado = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de pouso: {e}")

                    # Atualizar estado anterior
                    on_ground_anterior = on_ground


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
