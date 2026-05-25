import sys
import time
import json
import asyncio
import websockets
from threading import Thread
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QLabel, QProgressBar, QTextEdit
)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPen, QCursor, QImage
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject, QByteArray, QBuffer

class WebSocketClient(QObject):
    status_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    connection_lost = pyqtSignal()
    image_received = pyqtSignal(bytes)
    
    def __init__(self):
        super().__init__()
        self.url = "ws://192.168.4.1/cmd"
        self.websocket = None
        self.running = False
        self.reconnect_delay = 2
        self.loop = None
        self.thread = None
        
    def start(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self.run_event_loop, daemon=True)
        self.thread.start()
        
    def run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.connect_and_listen())
        self.loop.run_forever()
        
    async def connect_and_listen(self):
        while self.running:
            try:
                async with websockets.connect(
                    self.url, open_timeout=5, close_timeout=2, ping_interval=10
                ) as websocket:
                    self.websocket = websocket
                    self.connected.emit()
                    
                    async for message in websocket:
                        if isinstance(message, bytes):
                            self.handle_binary_message(message)
                        else:
                            self.handle_text_message(message)
                            
            except (websockets.exceptions.ConnectionClosed, 
                    websockets.exceptions.InvalidStatusCode,
                    ConnectionRefusedError,
                    TimeoutError, OSError,
                    asyncio.TimeoutError) as e:
                print(f"WebSocket disconnected: {type(e).__name__}")
                self.disconnected.emit()
                self.connection_lost.emit()
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                print(f"WebSocket error: {type(e).__name__}: {e}")
                self.disconnected.emit()
                self.connection_lost.emit()
                
            await asyncio.sleep(self.reconnect_delay)
            
    def handle_text_message(self, message):
        try:
            data = json.loads(message)
            self.status_received.emit(data)
        except json.JSONDecodeError:
            pass
            
    def handle_binary_message(self, message):
        if len(message) > 0:
            self.image_received.emit(message)
            
    def send_command(self, command):
        if self.websocket and self.running:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(command)), 
                self.loop
            )
            
    def stop(self):
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hexapod Controller")
        self.setStyleSheet("background-color: black;")
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(25)
        self.top_bar.setStyleSheet("background-color: transparent;")
        self.top_bar.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.top_layout = QHBoxLayout(self.top_bar)
        self.top_layout.setContentsMargins(10, 0, 10, 0)

        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("color: white; font-size: 12px;")
        self.fps_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.top_layout.addWidget(self.fps_label)
        self.top_layout.addSpacing(20)

        self.speed_label = QLabel("Speed: medium")
        self.speed_label.setStyleSheet("color: white; font-size: 12px;")
        self.speed_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.top_layout.addWidget(self.speed_label)
        self.top_layout.addSpacing(20)

        self.pitch_label = QLabel("Pitch: 0.0°")
        self.pitch_label.setStyleSheet("color: white; font-size: 12px;")
        self.pitch_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.top_layout.addWidget(self.pitch_label)
        self.top_layout.addSpacing(10)

        self.roll_label = QLabel("Roll: 0.0°")
        self.roll_label.setStyleSheet("color: white; font-size: 12px;")
        self.roll_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.top_layout.addWidget(self.roll_label)
        self.top_layout.addSpacing(10)

        self.yaw_label = QLabel("Yaw: 0.0°")
        self.yaw_label.setStyleSheet("color: white; font-size: 12px;")
        self.yaw_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.top_layout.addWidget(self.yaw_label)
        self.top_layout.addStretch()
        self.layout.addWidget(self.top_bar)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background-color: black;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setMouseTracking(True)
        self.view.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.layout.addWidget(self.view)
        self.pixmap_item = self.scene.addPixmap(QPixmap())
        self.last_image_data = None
        self.last_mouse_time = 0

        self.log_display = QTextEdit()
        self.log_display.setFixedWidth(220)
        self.log_display.setFixedHeight(350)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #00ff00;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                border: none;
                padding: 8px;
            }
        """)
        self.log_display.setReadOnly(True)
        self.log_display.setTextInteractionFlags(Qt.NoTextInteraction)
        self.log_display.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.log_display.move(10, 30)
        self.log_display.setParent(self.central_widget)
        self.log_display.show()

        self.bottom_left = QWidget()
        self.bottom_left.setFixedSize(150, 40)
        self.bottom_left.setStyleSheet("background-color: transparent;")
        self.bottom_left.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.bottom_left_layout = QHBoxLayout(self.bottom_left)
        self.bottom_left_layout.setContentsMargins(10, 0, 0, 10)

        self.battery_label = QLabel("Battery:")
        self.battery_label.setStyleSheet("color: white; font-size: 12px;")
        self.battery_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.bottom_left_layout.addWidget(self.battery_label)

        self.battery_bar = QProgressBar()
        self.battery_bar.setFixedWidth(80)
        self.battery_bar.setFixedHeight(15)
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(100)
        self.battery_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        self.battery_bar.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.bottom_left_layout.addWidget(self.battery_bar)
        self.bottom_left.move(0, 0)
        self.bottom_left.setParent(self.central_widget)
        self.bottom_left.show()

        self.log_items = []
        self.max_log_items = 8

        self.keys = {
            Qt.Key_W: False, Qt.Key_S: False,
            Qt.Key_A: False, Qt.Key_D: False,
            Qt.Key_Q: False, Qt.Key_E: False
        }
        self.shift_pressed = False
        self.gimbal_pan = 90
        self.gimbal_tilt = 90
        self.gimbal_sensitivity = 0.5
        self.last_operation_time = time.time()
        self.mouse_captured = False
        self.alt_pressed = False
        self.last_log_time = 0
        self.last_gimbal_send_time = 0
        
        self.base_speed = 0.5
        self.current_speed = 0.5
        self.last_sent_speed = None
        
        self.websocket_client = WebSocketClient()
        self.websocket_client.connected.connect(self.on_ws_connected)
        self.websocket_client.disconnected.connect(self.on_ws_disconnected)
        self.websocket_client.connection_lost.connect(self.on_ws_connection_lost)
        self.websocket_client.status_received.connect(self.on_ws_status_received)
        self.websocket_client.image_received.connect(self.on_ws_image_received)

        self.status_overlay = QLabel(self.view)
        self.status_overlay.setStyleSheet("color: red; font-size: 24px; font-weight: bold;")
        self.status_overlay.setAlignment(Qt.AlignCenter)
        self.status_overlay.show()
        self.status_overlay.setText("连接丢失")

        self.operation_timer = QTimer()
        self.operation_timer.timeout.connect(self.check_operation)
        self.operation_timer.start(500)

        self.mouse_control_timer = QTimer()
        self.mouse_control_timer.timeout.connect(self.update_mouse_control)
        self.mouse_control_timer.start(16)
        
        self.speed_control_timer = QTimer()
        self.speed_control_timer.timeout.connect(self.update_speed_control)
        self.speed_control_timer.start(50)
        
        self.movement_control_timer = QTimer()
        self.movement_control_timer.timeout.connect(self.update_movement_control)
        self.movement_control_timer.start(50)

        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)
        
        self.frame_count = 0
        self.last_fps_time = time.time()

        self.add_log("应用启动")
        self.add_log("正在连接机器人...")
        self.websocket_client.start()

    def add_log(self, text):
        self.log_items.append(text)
        if len(self.log_items) > self.max_log_items:
            self.log_items.pop(0)
        self.log_display.clear()
        for item in self.log_items:
            self.log_display.append(item)

    def keyPressEvent(self, event):
        key = event.key()
        
        if key == Qt.Key_W:
            self.keys[key] = True
            self.add_log("W - 前进")
            self.last_operation_time = time.time()
        elif key == Qt.Key_S:
            self.keys[key] = True
            self.add_log("S - 后退")
            self.last_operation_time = time.time()
        elif key == Qt.Key_A:
            self.keys[key] = True
            self.add_log("A - 左移")
            self.last_operation_time = time.time()
        elif key == Qt.Key_D:
            self.keys[key] = True
            self.add_log("D - 右移")
            self.last_operation_time = time.time()
        elif key == Qt.Key_Q:
            self.keys[key] = True
            self.add_log("Q - 左旋")
            self.last_operation_time = time.time()
        elif key == Qt.Key_E:
            self.keys[key] = True
            self.add_log("E - 右旋")
            self.last_operation_time = time.time()
        elif key == Qt.Key_Shift:
            self.shift_pressed = True
            self.add_log("Shift - 加速")
            self.last_operation_time = time.time()
        elif key == Qt.Key_Space:
            self.send_stop_command()
            self.add_log("Space - 停止")
            self.last_operation_time = time.time()
        elif key == Qt.Key_Escape:
            self.release_mouse()
        elif key == Qt.Key_F11:
            self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)
            self.add_log("F11 - 全屏切换")
            self.last_operation_time = time.time()
        elif key == Qt.Key_Alt:
            self.alt_pressed = True
            if self.mouse_captured:
                self.unsetCursor()
                self.add_log("Alt - 解除鼠标锁定")

    def keyReleaseEvent(self, event):
        key = event.key()
        if key in self.keys:
            self.keys[key] = False
        elif key == Qt.Key_Shift:
            self.shift_pressed = False
        elif key == Qt.Key_Alt:
            self.alt_pressed = False
            if self.mouse_captured:
                self.setCursor(Qt.BlankCursor)
                self.add_log("Alt - 恢复鼠标锁定")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.mouse_captured:
            self.capture_mouse()

    def mouseMoveEvent(self, event):
        pass

    def enterEvent(self, event):
        if not self.mouse_captured:
            self.capture_mouse()
        QMainWindow.enterEvent(self, event)

    def update_mouse_control(self):
        if not self.mouse_captured or self.alt_pressed:
            return
        
        try:
            window_center = QPoint(self.view.width() // 2, self.view.height() // 2)
            global_center = self.view.mapToGlobal(window_center)
            
            current_mouse_pos = QCursor.pos()
            delta_x = current_mouse_pos.x() - global_center.x()
            delta_y = current_mouse_pos.y() - global_center.y()
            
            if abs(delta_x) > 2 or abs(delta_y) > 2:
                pan_delta = delta_x * self.gimbal_sensitivity
                tilt_delta = -delta_y * self.gimbal_sensitivity
                
                new_pan = self.gimbal_pan + pan_delta
                new_tilt = self.gimbal_tilt + tilt_delta
                
                if 0 <= new_pan <= 180 and 0 <= new_tilt <= 180:
                    self.gimbal_pan = new_pan
                    self.gimbal_tilt = new_tilt
                    
                    current_time = time.time()
                    if abs(pan_delta) > 0.1 or abs(tilt_delta) > 0.1:
                        if current_time - self.last_log_time > 0.1:
                            log_text = ""
                            if abs(pan_delta) > 0.1:
                                log_text += f"Pan:{self.gimbal_pan:.0f}°"
                            if abs(tilt_delta) > 0.1:
                                if log_text:
                                    log_text += " "
                                log_text += f"Tilt:{self.gimbal_tilt:.0f}°"
                            self.add_log(log_text)
                            self.last_operation_time = current_time
                            self.last_log_time = current_time
                        
                        if current_time - self.last_gimbal_send_time > 0.05:
                            self.send_gimbal_command(int(self.gimbal_pan), int(self.gimbal_tilt))
                            self.last_gimbal_send_time = current_time
            
            QCursor.setPos(global_center)
        except Exception as e:
            print(f"Mouse control error: {e}")
    
    def send_gimbal_command(self, pan, tilt):
        self.websocket_client.send_command({'gimbal': {'pan': pan, 'tilt': tilt}})

    def capture_mouse(self):
        if self.mouse_captured:
            return
        try:
            self.mouse_captured = True
            self.setCursor(Qt.BlankCursor)
            window_center = QPoint(self.view.width() // 2, self.view.height() // 2)
            QCursor.setPos(self.view.mapToGlobal(window_center))
            self.add_log("鼠标已捕获 - 移动控制云台")
        except Exception as e:
            print(f"Capture mouse error: {e}")
            self.mouse_captured = False

    def release_mouse(self):
        if not self.mouse_captured:
            return
        try:
            self.mouse_captured = False
            self.unsetCursor()
            self.add_log("鼠标已释放")
        except Exception as e:
            print(f"Release mouse error: {e}")

    def update_speed_control(self):
        new_speed = 1.0 if self.shift_pressed else self.base_speed
        
        if new_speed != self.current_speed:
            self.current_speed = new_speed
            speed_text = "fast" if self.current_speed == 1.0 else "medium"
            self.speed_label.setText(f"Speed: {speed_text}")
            
            if new_speed != self.last_sent_speed:
                self.send_speed_command(new_speed)
                self.last_sent_speed = new_speed

    def send_speed_command(self, speed):
        self.add_log(f"Speed: {speed}")
        self.websocket_client.send_command({'speed': speed})

    def update_movement_control(self):
        if not self.websocket_client.websocket:
            return
            
        command = 0
        has_movement = False
        
        if self.keys[Qt.Key_W]:
            command |= (1 << 1)
            has_movement = True
        if self.keys[Qt.Key_S]:
            command |= (1 << 3)
            has_movement = True
        if self.keys[Qt.Key_A]:
            command |= (1 << 6)
            has_movement = True
        if self.keys[Qt.Key_D]:
            command |= (1 << 7)
            has_movement = True
        if self.keys[Qt.Key_Q]:
            command |= (1 << 4)
            has_movement = True
        if self.keys[Qt.Key_E]:
            command |= (1 << 5)
            has_movement = True
            
        if has_movement:
            self.websocket_client.send_command({'movementMode': command})

    def send_stop_command(self):
        self.websocket_client.send_command({'stop': True})

    def check_operation(self):
        current_time = time.time()
        if current_time - self.last_operation_time > 2.0:
            self.add_log("no Operation")

    def on_ws_connected(self):
        self.add_log("WebSocket已连接")
        self.status_overlay.hide()
        
    def on_ws_disconnected(self):
        self.add_log("WebSocket已断开")
        
    def on_ws_connection_lost(self):
        self.status_overlay.show()
        self.status_overlay.setText("连接丢失")
        
    def on_ws_status_received(self, data):
        if 'power' in data:
            self.update_battery(data['power'])
        if 'imu' in data:
            self.update_imu(data['imu'])

    def on_ws_image_received(self, image_data):
        try:
            self.frame_count += 1
            self.last_image_data = image_data
            self.update_image_display()
        except Exception as e:
            print(f"Image decode error: {e}")

    def update_image_display(self):
        if not self.last_image_data:
            return
        try:
            image = QImage.fromData(self.last_image_data)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                view_size = self.view.size()
                scaled = pixmap.scaled(view_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.pixmap_item.setPixmap(scaled)
                self.scene.setSceneRect(0, 0, scaled.width(), scaled.height())
                self.view.centerOn(scaled.width() / 2, scaled.height() / 2)
        except Exception as e:
            print(f"Image display error: {e}")

    def update_fps(self):
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        if elapsed > 0:
            fps = int(self.frame_count / elapsed)
            self.fps_label.setText(f"FPS: {fps}")
        self.frame_count = 0
        self.last_fps_time = current_time

    def update_battery(self, power_data):
        if 'voltage' in power_data:
            voltage = power_data['voltage']
            percentage = min(100, max(0, ((voltage - 3.0) / (4.2 - 3.0)) * 100))
            self.battery_bar.setValue(int(percentage))
            self.add_log(f"Battery: {voltage:.2f}V ({int(percentage)}%)")
            
    def update_imu(self, imu_data):
        if 'pitch' in imu_data:
            self.pitch_label.setText(f"Pitch: {imu_data['pitch']:.1f}°")
        if 'roll' in imu_data:
            self.roll_label.setText(f"Roll: {imu_data['roll']:.1f}°")
        if 'yaw' in imu_data:
            self.yaw_label.setText(f"Yaw: {imu_data['yaw']:.1f}°")

    def resizeEvent(self, event):
        self.view.setGeometry(0, 0, self.central_widget.width(), self.central_widget.height())
        self.scene.setSceneRect(0, 0, self.view.width(), self.view.height())
        self.update_image_display()
        self.bottom_left.move(10, self.central_widget.height() - 50)
        self.status_overlay.resize(self.view.size())

    def paintEvent(self, event):
        QMainWindow.paintEvent(self, event)
        painter = QPainter(self)
        
        view_rect = self.view.geometry()
        center_x = view_rect.left() + view_rect.width() // 2
        center_y = view_rect.top() + view_rect.height() // 2
        line_length = 20
        
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(center_x - line_length, center_y, center_x + line_length, center_y)
        painter.drawLine(center_x, center_y - line_length, center_x, center_y + line_length)

    def closeEvent(self, event):
        self.websocket_client.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.activateWindow()
    window.setFocus()
    sys.exit(app.exec_())
