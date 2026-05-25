# OpenMV 图像传输集成更新日志

## 版本

NodeHexa v2.1.0 — OpenMV Camera Integration

---

## 物理接线

| OpenMV Cam H7 Plus | NodeMCU ESP32 | 说明 |
|---|---|---|
| **P4** (UART3 TX) | **GPIO33** | 图像数据传输 |
| **P5** (UART3 RX) | **GPIO32** | 双向通讯（预留） |
| **GND** | **GND** | 必须共地 |

> 注：ESP32 的 Serial1 被配置为 `RX=GPIO33, TX=GPIO32`，与 OpenMV P4(TX)/P5(RX) 交叉连接。UART 波特率 115200。

---

## 新增功能

### 1. OpenMV → ESP32 图像传输

- **OpenMV 端** (`openmv_firmware/image_sender.py`)
  - 采集 QQVGA (160x120) 图像
  - JPEG 压缩（quality=50），单帧约 1.8KB
  - 帧协议封装：`0xFF 0xAA` + 4字节长度(LE) + JPEG数据 + `0xFF 0xBB`
  - 帧率约 6 FPS

- **ESP32 端** (`firmware/src/main.cpp`)
  - 新增 `OpenMVReceiveTask` FreeRTOS 任务
  - 状态机解析帧协议：IDLE → START → LENGTH → DATA → END
  - 32KB 帧缓冲区
  - 接收完整帧后通过 WebSocket 广播

### 2. ESP32 → 桌面应用 WebSocket 图像推送

- ESP32 通过 `/cmd` WebSocket 端点以**二进制帧**推送 JPEG 数据
- 桌面应用 (`desktop_app_python/main.py`) 自动接收并解码显示
- 图像自动缩放铺满窗口，保持宽高比
- 支持窗口缩放时自动适配
- 自动重连机制

### 3. 桌面应用 UI

- **PyQt5** 图形界面
- 实时图像显示（背景层）
- 悬浮 UI 层：FPS、姿态角度、电池电量、日志
- 键盘 WASD/QE 运动控制 + 鼠标云台控制
- 准星瞄准线

---

## Bug 修复

### PCA9685 启动崩溃

- **问题**：`PCA9685` 构造函数在全局初始化阶段调用 `new Adafruit_PWMServoDriver()`，此时 ESP32 内存分配器未就绪，导致启动崩溃
- **修复**：将 `Adafruit_PWMServoDriver` 对象创建推迟到 `begin()` 方法（lazy initialization）
- **文件**：`firmware/lib/hal/pwm.h`, `firmware/lib/hal/pwm.cpp`

### OpenMV UART API 兼容性

- OpenMV v4.5.9 (MicroPython v1.23.0) 需使用 `pyb.UART` 而非 `machine.UART`
- `pyb.LED` 使用整数参数 (1=红, 2=绿, 3=蓝)

### 帧解析 END 状态 Bug

- **问题**：END 状态收到 `0xFF`（结束标记首字节）后无条件回到 IDLE，导致 `0xBB` 被丢弃
- **修复**：仅在收到 `0xBB` 时完成帧并回 IDLE，收到 `0xFF` 时保持 END 状态

---

## 修改文件清单

| 文件 | 变更类型 | 说明 |
|---|---|---|
| `firmware/src/main.cpp` | 修改 | 添加 Serial1 初始化 + OpenMVReceiveTask 帧接收器 |
| `firmware/lib/hal/pwm.h` | 修改 | 添加 i2cAddress_ 成员 |
| `firmware/lib/hal/pwm.cpp` | 修改 | Lazy init: 推迟 Adafruit_PWMServoDriver 创建 |
| `firmware/platformio.ini` | 修改 | 添加 upload_speed 配置 |
| `openmv_firmware/image_sender.py` | 新增 | OpenMV 图像采集发送脚本 |
| `openmv_firmware/simple_test.py` | 新增 | OpenMV UART 通讯测试脚本 |
| `desktop_app_python/main.py` | 新增 | PyQt5 桌面控制应用 |
| `desktop_app_python/requirements.txt` | 新增 | Python 依赖 |

---

## ESP32 串口资源分配

| 串口 | 引脚 | 用途 |
|---|---|---|
| Serial (UART0) | USB | 调试输出 |
| Serial1 (UART1) | GPIO33(RX), GPIO32(TX) | OpenMV 摄像头通讯 |
| Serial2 (UART2) | GPIO16(RX), GPIO17(TX) | 运动指令 |

---

## 桌面应用依赖

```bash
pip install PyQt5 websockets
```

## 使用方法

1. OpenMV 运行 `image_sender.py`
2. ESP32 上电启动（自动连接 OpenMV）
3. 电脑连接 `NodeHexa-7000` WiFi
4. 运行 `python main.py`