# 🦿 Hexapod Smart System - 六足智能系统

> 本文档是 Hexapod Smart System 项目的核心开发文档，记录所有功能模块的开发进展、待解决问题和技术架构。

---

## 📋 项目概述

Hexapod Smart System 是一个开源的六足机器人智能扩展系统，基于 NodeHexa 硬件平台，集成多种控制方式和智能功能模块。

### 🎯 项目目标

- **多样化控制** - 支持 Xbox 手柄、Web界面、串口指令等多种控制方式
- **智能扩展** - 集成摄像头、传感器等智能模块
- **桌面集成** - 开发桌面端控制软件，实现更强大的功能
- **模块化设计** - 各功能模块独立开发，易于维护和扩展

### 📦 当前支持的功能模块

| 模块 | 状态 | 说明 |
|------|------|------|
| Xbox 手柄控制 | ✅ 已完成 | 蓝牙连接、摇杆映射、速度控制 |
| Web 控制界面 | ✅ 已完成 | 运动控制、校准系统、运动规划 |
| 串口通信 | ✅ 已完成 | UART2 指令协议 |
| 摄像头扩展 | 🔨 开发中 | 视觉模块集成 |
| 桌面端软件 | 📋 计划中 | Python/C++ 桌面应用 |

---

## 📁 项目结构

```
NodeHexa-2.1.0/
├── firmware/                          # 嵌入式固件
│   ├── src/                          # 源代码
│   │   ├── main.cpp                 # 主程序
│   │   ├── gamepad_controller.cpp   # Xbox手柄控制
│   │   ├── hexapod.cpp             # 六足运动控制
│   │   └── ...
│   ├── data/                        # Web界面文件
│   │   ├── web_controller.html      # Web控制界面
│   │   ├── calibration.html         # 校准界面
│   │   └── ...
│   ├── lib/                         # 第三方库
│   └── XBOX_GAMEPAD_DEVELOPMENT.md  # Xbox手柄开发文档
│
├── desktop/                          # 桌面端软件（待创建）
│   ├── python/                      # Python实现
│   └── cpp/                         # C++实现
│
├── camera/                           # 摄像头模块（待创建）
│   ├── hardware/                    # 硬件设计
│   └── software/                    # 驱动和算法
│
└── docs/                            # 文档
    └── HEXAPOD_SMART_SYSTEM.md      # 本文档
```

---

## 🛠️ 技术架构

### 1. 固件层 (Firmware)

**硬件平台**
- 主控: ESP32 (NodeMCU-32S)
- 舵机驱动: PCA9685 PWM
- 通信: WiFi + UART2 + Bluetooth (Xbox手柄)

**核心模块**
- 运动控制: 正逆运动学、步态生成
- 输入处理: 手柄解析、WebSocket、串口指令
- 存储管理: Flash校准数据、SPIFFS文件系统

### 2. 通信层 (Communication)

| 接口 | 协议 | 用途 |
|------|------|------|
| WiFi AP | HTTP/WebSocket | Web控制界面 |
| Bluetooth | BLE/NimBLE | Xbox手柄连接 |
| UART2 | 自定义指令集 | 串口调试和桌面通信 |

### 3. 应用层 (Application)

- **控制模式**: 手柄模式 / Web模式 / 串口模式
- **智能模块**: 摄像头视觉处理（待开发）
- **桌面软件**: Python/C++ 应用（待开发）

---

## ✅ 已完成功能

### Xbox 手柄控制
- ✅ 蓝牙连接和自动重连
- ✅ 摇杆值读取和死区过滤
- ✅ 轴值归一化（修复边缘值问题）
- ✅ 方向优先级逻辑
- ✅ RT速度控制 + RB速度模式切换
- ✅ 集成到主程序

### Web 控制界面
- ✅ 运动控制界面
- ✅ 实时校准系统
- ✅ 运动规划和动作序列
- ✅ 电量监测和保护

### 通信系统
- ✅ WebSocket 低延迟通信
- ✅ UART2 串口指令协议
- ✅ BLE 蓝牙广播和连接

---

## 🔨 开发中功能

### 摄像头扩展
- [ ] 硬件选型和接口设计
- [ ] 图像采集驱动
- [ ] 视觉处理算法
- [ ] 与主系统集成

### 桌面端软件
- [ ] Python 原型开发
- [ ] C++ 性能优化版本
- [ ] 跨平台支持
- [ ] 高级控制功能

---

## 📋 待开发功能

### 高优先级
- [ ] 单腿控制模式（Xbox手柄LT激活）
- [ ] Web蓝牙控制开关
- [ ] 死区参数动态调优

### 中优先级
- [ ] 摄像头视觉模块
- [ ] 桌面端控制软件
- [ ] 传感器融合（陀螺仪、加速度计）

### 低优先级
- [ ] 语音控制集成
- [ ] 自主导航算法
- [ ] 多机器人协同

---

## 📖 详细开发文档

各功能模块的详细开发记录请参考：

- [Xbox 手柄控制开发文档](firmware/XBOX_GAMEPAD_DEVELOPMENT.md)
- [单腿控制模式需求](firmware/XBOX_GAMEPAD_DEVELOPMENT.md#22-单腿控制模式)
- [摄像头模块设计（待创建）](camera/README.md)

---

## 🔧 开发环境

### 固件开发
- **IDE**: VSCode + PlatformIO插件
- **框架**: Arduino for ESP32
- **工具链**: ESP-IDF, esptool

### 桌面软件开发
- **Python版本**: 3.8+
- **C++标准**: C++17
- **跨平台**: Windows/Linux/macOS

---

## 📝 修改日志

| 日期 | 版本 | 修改内容 |
|------|------|----------|
| 2026-05-23 | v1.0 | 创建Hexapod Smart System项目主文档 |

---

## 🤝 参与贡献

欢迎提交Issue和Pull Request来改进项目！

---

## 📄 许可证

本项目基于 GPL-3.0 许可证开源。

---

## 👤 作者

- **GitHub**: [@Rihyokin](https://github.com/Rihyokin)
- **项目仓库**: [Nodehexa-Control-by-xboxControlle](https://github.com/Rihyokin/Nodehexa-Control-by-xboxControlle)

---

**🦿 让六足机器人更智能！**
