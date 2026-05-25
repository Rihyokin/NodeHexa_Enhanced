import sys
import serial
import serial.tools.list_ports
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLineEdit, QLabel
)
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject

class SerialThread(QObject):
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    
    def __init__(self, port, baud_rate):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.running = False
        self.thread = None
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        
    def run(self):
        try:
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.connection_status.emit(True)
            
            while self.running and self.serial.is_open:
                try:
                    data = self.serial.readline().decode('utf-8', errors='ignore')
                    if data:
                        self.data_received.emit(data)
                except Exception as e:
                    pass
                    
        except Exception as e:
            self.connection_status.emit(False)
            
    def stop(self):
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
            
    def send(self, data):
        if self.serial and self.serial.is_open:
            self.serial.write(data.encode('utf-8'))

class SerialMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32 Serial Monitor")
        self.setGeometry(100, 100, 800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.top_bar = QWidget()
        self.top_layout = QHBoxLayout(self.top_bar)
        
        self.port_label = QLabel("端口:")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        
        self.baud_label = QLabel("波特率:")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400"])
        self.baud_combo.setCurrentText("115200")
        
        self.refresh_btn = QPushButton("刷新端口")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.top_layout.addWidget(self.port_label)
        self.top_layout.addWidget(self.port_combo)
        self.top_layout.addSpacing(20)
        self.top_layout.addWidget(self.baud_label)
        self.top_layout.addWidget(self.baud_combo)
        self.top_layout.addSpacing(20)
        self.top_layout.addWidget(self.refresh_btn)
        self.top_layout.addWidget(self.connect_btn)
        self.top_layout.addStretch()
        
        self.layout.addWidget(self.top_bar)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setStyleSheet("background-color: black; color: #00ff00;")
        self.layout.addWidget(self.output_text)
        
        self.bottom_bar = QWidget()
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入命令...")
        self.input_line.returnPressed.connect(self.send_command)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_command)
        
        self.clear_btn = QPushButton("清屏")
        self.clear_btn.clicked.connect(self.clear_output)
        
        self.bottom_layout.addWidget(self.input_line)
        self.bottom_layout.addWidget(self.send_btn)
        self.bottom_layout.addWidget(self.clear_btn)
        
        self.layout.addWidget(self.bottom_bar)
        
        self.serial_thread = None
        self.connected = False
        
        self.refresh_ports()
        
    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")
            
    def toggle_connection(self):
        if not self.connected:
            if not self.port_combo.currentText():
                self.append_text("请选择串口端口")
                return
                
            port = self.port_combo.currentText().split(" - ")[0]
            baud = int(self.baud_combo.currentText())
            
            self.serial_thread = SerialThread(port, baud)
            self.serial_thread.data_received.connect(self.append_text)
            self.serial_thread.connection_status.connect(self.on_connection_status)
            self.serial_thread.start()
            
            self.connect_btn.setText("断开")
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
        else:
            if self.serial_thread:
                self.serial_thread.stop()
                self.serial_thread = None
                
            self.connect_btn.setText("连接")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.connected = False
            self.append_text("已断开连接")
            
    def on_connection_status(self, connected):
        self.connected = connected
        if connected:
            self.append_text(f"已连接到 {self.port_combo.currentText().split(' - ')[0]}")
        else:
            self.append_text("连接失败，请检查端口是否被占用")
            self.connect_btn.setText("连接")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            
    def append_text(self, text):
        self.output_text.moveCursor(QTextCursor.End)
        self.output_text.insertPlainText(text)
        self.output_text.moveCursor(QTextCursor.End)
        
    def send_command(self):
        if not self.connected:
            self.append_text("未连接，请先连接串口\n")
            return
            
        command = self.input_line.text()
        if command:
            self.serial_thread.send(command + "\n")
            self.append_text(f"> {command}\n")
            self.input_line.clear()
            
    def clear_output(self):
        self.output_text.clear()
        
    def closeEvent(self, event):
        if self.serial_thread:
            self.serial_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialMonitor()
    window.show()
    sys.exit(app.exec_())