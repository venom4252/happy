import sys
import os
import socket
import threading
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox
)

MATCHMAKER_URL = "https://your-matchmaker-server.onrender.com/connect"

class FileReceiver(threading.Thread):
    def __init__(self, save_path, port=5001):
        super().__init__(daemon=True)
        self.save_path = save_path
        self.port = port

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", self.port))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                filename = conn.recv(1024).decode()
                filepath = os.path.join(self.save_path, filename)
                with open(filepath, 'wb') as f:
                    while chunk := conn.recv(4096):
                        f.write(chunk)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P2P File Sender")
        self.setGeometry(300, 300, 400, 200)
        self.setup_ui()
        self.save_path = ""

    def setup_ui(self):
        layout = QVBoxLayout()

        self.name_label = QLabel("Твой ник:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        self.peer_label = QLabel("Ник собеседника:")
        self.peer_input = QLineEdit()
        layout.addWidget(self.peer_label)
        layout.addWidget(self.peer_input)

        self.path_btn = QPushButton("Выбрать папку загрузки")
        self.path_btn.clicked.connect(self.choose_path)
        layout.addWidget(self.path_btn)

        self.connect_btn = QPushButton("Соединиться")
        self.connect_btn.clicked.connect(self.connect)
        layout.addWidget(self.connect_btn)

        self.status = QLabel("")
        layout.addWidget(self.status)

        self.setLayout(layout)

    def choose_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.save_path = folder
            self.path_btn.setText(f"📁 {folder}")

    def connect(self):
        if not all([self.name_input.text(), self.peer_input.text(), self.save_path]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля и выберите папку.")
            return

        self.status.setText("⏳ Ожидание второго участника...")
        threading.Thread(target=self.match_and_receive, daemon=True).start()

    def match_and_receive(self):
        # 1. Отправляем на Matchmaker сервер
        response = requests.post(MATCHMAKER_URL, json={
            "self": self.name_input.text(),
            "peer": self.peer_input.text(),
            "port": 5001
        })

        if response.status_code == 200:
            peer_info = response.json()
            if peer_info["role"] == "receiver":
                self.status.setText("📥 Ждём входящий файл...")
                FileReceiver(self.save_path).start()
            elif peer_info["role"] == "sender":
                self.status.setText("📤 Отправка файла...")
                self.send_file(peer_info["ip"], peer_info["port"])

    def send_file(self, ip, port):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
        if not file_path:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.send(os.path.basename(file_path).encode())
                with open(file_path, 'rb') as f:
                    while chunk := f.read(4096):
                        s.send(chunk)
            self.status.setText("✅ Файл отправлен!")
        except Exception as e:
            self.status.setText(f"Ошибка: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
