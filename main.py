import sys
import threading
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLabel,
    QStatusBar,
    QFrame,
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QSize
from SimConnect import *
import time
import pygame
import platform


import os
import sys

def resource_path(relative_path):
    """Retorna o caminho absoluto, funciona no PyInstaller e em execução normal."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

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
        motores_desligados_tocado = False
        pouso_realizado = False
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
                    engine1_on = aircraft.get("GENERAL_ENG_COMBUSTION:1") or 0
                    engine2_on = aircraft.get("GENERAL_ENG_COMBUSTION:2") or 0
                    ground_speed_knots = ground_speed * 1.94384
                    voo_realizado = False

                    # self.update_callback(f"[DEBUG] Alt: {altitude:.0f} | Vel: {speed:.0f} | GS: {ground_speed:.1f} | STROBE: {strobe_on} | VS: {vertical_speed} | OnGround: {on_ground}")
                    # .update_callback(f"[DEBUG] {on_ground} | GS: {ground_speed} | E1: {engine1_on} | E2: {engine2_on}")

                    # Áudio 1: Embarque (com try para detectar erro real)

                    if voltage > 1 and not embarque_tocado:
                        try:
                            pygame.mixer.music.load(resource_path("audio/01_Embarque.mp3"))
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Embarque")
                            embarque_tocado = True
                            tempo_embarque = time.time()
                        except Exception as e:
                            self.update_callback(
                                f"⚠️ Erro ao tocar áudio de embarque: {e}"
                            )
                            embarque_tocado = False  # não marca como tocado se der erro
                    # Áudio 2: Boas Vindas (somente se embarque foi tocado com sucesso)

                    if embarque_tocado and not boasvindas_tocado:
                        if tempo_embarque and time.time() - tempo_embarque >= 120:
                            try:
                                pygame.mixer.music.load(resource_path("audio/02_BoasVindas.mp3"))
                                pygame.mixer.music.play()
                                self.update_callback("[✔️] Boas-vindas")
                                boasvindas_tocado = True
                            except Exception as e:
                                self.update_callback(
                                    f"⚠️ Erro ao tocar áudio de boas-vindas: {e}"
                                )
                    # Áudio 3: Segurança (quando velocidade no solo > 5)

                    if ground_speed_knots > 3 and not seguranca_tocado:
                        try:
                            pygame.mixer.music.load(resource_path(
                                "audio/03_Seguranca.mp3"
                            ))  # renomeado
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Áudio de segurança")
                            seguranca_tocado = True
                        except Exception as e:
                            self.update_callback(
                                f"⚠️ Erro ao tocar áudio de segurança: {e}"
                            )
                    # Áudio 4: Taxiamento (quando ground speed > 10, mas só uma vez)

                    if ground_speed_knots > 10 and not taxiamento_tocado:
                        try:
                            pygame.mixer.music.load(resource_path("audio/04_Taxiamento.mp3"))
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Taxiamento iniciado")
                            taxiamento_tocado = True
                        except Exception as e:
                            self.update_callback(
                                f"⚠️ Erro ao tocar áudio de taxiamento: {e}"
                            )
                    # Áudio 5: Preparação para decolagem (quando strobe ON)
                    # Áudio 5: Preparação para decolagem (só toca se taxiamento foi feito E strobe ligado E aeronave não está mais parada)

                    if taxiamento_tocado and not preparacao_tocada:
                        if strobe_on == 1 and ground_speed_knots > 5:
                            try:
                                pygame.mixer.music.load(resource_path(
                                    "audio/05_PreparemTripulacao.mp3")
                                )
                                pygame.mixer.music.play()
                                self.update_callback("[✔️] Preparação para decolagem")
                                preparacao_tocada = True
                            except Exception as e:
                                self.update_callback(
                                    f"⚠️ Erro ao tocar áudio de preparação: {e}"
                                )
                    # Áudio 6: Passagem de 10.000 pés

                    if altitude > 10000 and not audio10000_tocado:
                        try:
                            pygame.mixer.music.load(resource_path("audio/06_10000Pes.mp3"))
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Acima de 10.000 pés")
                            audio10000_tocado = True
                        except Exception as e:
                            self.update_callback(
                                f"⚠️ Erro ao tocar áudio de 10.000 pés: {e}"
                            )
                    # Condições para áudio de cruzeiro

                    if altitude > 13000:
                        if (
                            ultima_altitude is not None
                            and abs(altitude - ultima_altitude) < 30
                        ):
                            tempo_nivelado += 2  # 2 segundos por iteração do loop
                        else:
                            tempo_nivelado = 0
                        ultima_altitude = altitude

                        vertical_speed = aircraft.get("VERTICAL_SPEED") or 0

                        if (
                            (abs(vertical_speed) < 100)
                            and (tempo_nivelado >= 60)
                            and not cruzeiro_tocado
                        ):
                            try:
                                pygame.mixer.music(resource_path("audio/07_Cruzeiro.mp3"))
                                pygame.mixer.music.play()
                                self.update_callback("[✔️] Cruzeiro alcançado")
                                cruzeiro_tocado = True
                            except Exception as e:
                                self.update_callback(
                                    f"⚠️ Erro ao tocar áudio de cruzeiro: {e}"
                                )
                    # Debug

                    # Detecta início da descida real

                    if (
                        not descida_tocada
                        and cruzeiro_tocado
                        and altitude < 15000
                        and vertical_speed < -500  # velocidade de descida bem evidente
                    ):
                        try:
                            pygame.mixer.music.load(resource_path("audio/08_Descida.mp3"))
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Descida iniciada")
                            descida_tocada = True
                        except Exception as e:
                            self.update_callback(
                                f"⚠️ Erro ao tocar áudio de descida: {e}"
                            )
                    # Detectar toque no solo

                    if (
                        on_ground
                        and not on_ground_anterior
                        and ground_speed_knots > 30
                        and not pouso_tocado
                    ):
                        tempo_no_solo = time.time()
                    # Se está no solo há mais de 15 segundos e ainda não tocou o áudio

                    if (
                        on_ground
                        and tempo_no_solo
                        and time.time() - tempo_no_solo >= 15
                        and not pouso_tocado
                    ):
                        try:
                            pygame.mixer.music.load(resource_path("audio/09_Pouso.mp3"))
                            pygame.mixer.music.play()
                            self.update_callback("[✔️] Pouso confirmado")
                            pouso_tocado = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio de pouso: {e}")
                    # Atualizar estado anterior

                    on_ground_anterior = on_ground

                    # Desligamento dos motores
                    # Marcar que o voo realmente começou

                    if altitude > 10000:
                        voo_realizado = True
                    # Detectar pouso (somente se o voo aconteceu)

                    if (
                        voo_realizado
                        and not pouso_realizado
                        and on_ground
                        and vertical_speed < 0
                        and altitude < 1000
                    ):
                        pouso_realizado = True
                        self.update_callback("[DEBUG] Pouso detectado com sucesso")
                    # Áudio final apenas se voo e pouso ocorreram

                    if (
                        voo_realizado
                        and pouso_realizado
                        and not motores_desligados_tocado
                        and on_ground
                        and ground_speed < 5
                        and not engine1_on
                        and not engine2_on
                    ):
                        try:
                            pygame.mixer.music.load(resource_path("audio/10_Final.mp3"))
                            pygame.mixer.music.play()
                            self.update_callback(
                                "[✔️] Motores desligados detectado após o pouso"
                            )
                            motores_desligados_tocado = True
                        except Exception as e:
                            self.update_callback(f"⚠️ Erro ao tocar áudio final: {e}")
                    # Reiniciar toques se a aeronave estiver no solo
                except Exception as e:
                    self.update_callback(f"⚠️ Erro ao ler dados da aeronave: {e}")
                time.sleep(2)
        except ConnectionError:
            self.update_callback("🔴 Não foi possível conectar ao MSFS2020.")
        except Exception as e:
            self.update_callback(f"❌ Erro inesperado: {str(e)}")

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlightDeckSounds- MSFS2020/24")
        self.setFixedSize(700, 500)
        self.worker = None
        self.initUI()
        self.center_window()

    def center_window(self):
        frame = self.frameGeometry()
        center_point = QApplication.desktop().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def initUI(self):
        # Configuração geral da janela

        self.setWindowIcon(QIcon("assets/icon.png"))  # Substitua por um ícone real
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #2C3E50;
            }
        """
        )

        # Widget central

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 10)
        main_layout.setSpacing(15)

        # Cabeçalho

        header = QLabel("FlightDeckSounds - MSFS2020/24 ")
        header.setStyleSheet(
            """
            QLabel {
                color: #ECF0F1;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
        """
        )
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Separador

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #7F8C8D;")
        main_layout.addWidget(separator)

        # Área de exibição

        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setStyleSheet(
            """
            QTextEdit {
                background-color: #34495E;
                color: #ECF0F1;
                border: 1px solid #7F8C8D;
                border-radius: 5px;
                padding: 10px;
            }
        """
        )
        self.display.setFont(QFont("Consolas", 10))

        # Adicionar informações iniciais

        self.display.append("🛫 MSFS2020 - Áudio de Cabine")
        self.display.append(f"📦 Versão: 1.0.0")
        self.display.append(f"💻 Sistema: {platform.system()} {platform.release()}")
        self.display.append(f"🐍 Python: {platform.python_version()}")
        self.display.append("\n🔧 Aguardando conexão com o simulador...")

        main_layout.addWidget(self.display)

        # Painel de botões

        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)

        self.connect_btn = QPushButton("Conectar ao Simulador")
        self.stop_btn = QPushButton("Parar Conexão")

        # Configurar botões

        for btn in [self.connect_btn, self.stop_btn]:
            btn.setFont(QFont("Arial", 11, QFont.Bold))
            btn.setMinimumHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #27AE60;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #2ECC71;
            }
            QPushButton:pressed {
                background-color: #219653;
            }
        """
        )

        self.stop_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #EC7063;
            }
            QPushButton:pressed {
                background-color: #C0392B;
            }
        """
        )
        self.stop_btn.setEnabled(False)

        # Ícones para os botões

        self.connect_btn.setIcon(
            QIcon("assets/connect.png")
        )  # Substitua por ícones reais
        self.stop_btn.setIcon(QIcon("assets/stop.png"))
        self.connect_btn.setIconSize(QSize(20, 20))
        self.stop_btn.setIconSize(QSize(20, 20))

        # Conectar sinais

        self.connect_btn.clicked.connect(self.start_connection)
        self.stop_btn.clicked.connect(self.stop_connection)

        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.stop_btn)
        main_layout.addWidget(button_panel)

        # Barra de status

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")

        # Separador inferior

        separator_bottom = QFrame()
        separator_bottom.setFrameShape(QFrame.HLine)
        separator_bottom.setFrameShadow(QFrame.Sunken)
        separator_bottom.setStyleSheet("color: #7F8C8D;")
        main_layout.addWidget(separator_bottom)

        # Rodapé

        footer = QLabel("© 2025 FlightDeckSounds | Desenvolvido por Dalmo dos Santos Carbral")
        footer.setStyleSheet(
            """
            QLabel {
                color: #BDC3C7;
                font-size: 10px;
            }
        """
        )
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    def start_connection(self):
        if not self.worker or not self.worker.is_alive():
            self.display.clear()
            self.display.append("🔄 Conectando ao Microsoft Flight Simulator 2020...")
            self.status_bar.showMessage("Conectando...")

            self.worker = SimConnectWorker(self.update_display)
            self.worker.start()

            self.connect_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

    def stop_connection(self):
        if self.worker:
            self.worker.stop()
            self.display.append("⛔ Conexão encerrada pelo usuário.")
            self.status_bar.showMessage("Desconectado")

            self.connect_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.worker = None

    def update_display(self, message, msg_type="info"):
        if msg_type == "error":
            color = "#E74C3C"
        elif msg_type == "success":
            color = "#2ECC71"
        else:
            color = "#3498DB"
        self.display.append(f'<span style="color:{color}">{message}</span>')
        self.status_bar.showMessage(message)

        # Rolagem automática para baixo

        self.display.verticalScrollBar().setValue(
            self.display.verticalScrollBar().maximum()
        )

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.join(timeout=1)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Definir estilo geral

    app.setStyle("Fusion")

    # Configurar paleta de cores

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
