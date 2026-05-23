#include "gamepad_controller.h"

#include <cmath>

#include "debug.h"
#include "config.h"

namespace gamepad {

static MotionCommand g_motionCommand = {};

Controller& Controller::instance() {
    static Controller inst;
    return inst;
}

Controller& controller() {
    return Controller::instance();
}

void Controller::begin(const char* xboxMacAddress) {
    if (!mutex_) {
        mutex_ = xSemaphoreCreateMutex();
    }

    isConnected_ = false;
    isConnecting_ = false;
    emergencyStopRequested_ = false;

    xboxController_ = new XboxSeriesXControllerESP32_asukiaaa::Core(xboxMacAddress);

    LOG_INFO("Gamepad controller initialized with MAC: %s", xboxMacAddress);
}

void Controller::onLoopTick() {
    if (xSemaphoreTake(mutex_, portMAX_DELAY) != pdTRUE) {
        return;
    }

    if (xboxController_) {
        static int loopCount = 0;
        xboxController_->onLoop();

        bool wasConnected = isConnected_;
        isConnected_ = xboxController_->isConnected();
        isConnecting_ = xboxController_->isWaitingForFirstNotification();

        loopCount++;
        if (loopCount % 100 == 0) {
            LOG_INFO("onLoop #%d: isConnected=%d, isConnecting=%d",
                     loopCount, isConnected_, isConnecting_);
        }

        if (isConnected_ && !wasConnected) {
            LOG_INFO("Xbox controller connected!");
        } else if (!isConnected_ && wasConnected) {
            LOG_INFO("Xbox controller disconnected");
        }
    }

    if (isConnected_) {
        updateMotionCommand();
    }

    xSemaphoreGive(mutex_);
}

bool Controller::isConnected() const {
    return isConnected_;
}

bool Controller::isConnecting() const {
    return isConnecting_;
}

int16_t Controller::getLeftStickX() const {
    if (!xboxController_ || !isConnected_) return 0;
    return leftStickXToSigned(xboxController_->xboxNotif.joyLHori);
}

int16_t Controller::getLeftStickY() const {
    if (!xboxController_ || !isConnected_) return 0;
    return leftStickYToSigned(xboxController_->xboxNotif.joyLVert);
}

int16_t Controller::getRightStickX() const {
    if (!xboxController_ || !isConnected_) return 0;
    return rightStickXToSigned(xboxController_->xboxNotif.joyRHori);
}

int16_t Controller::getRightStickY() const {
    if (!xboxController_ || !isConnected_) return 0;
    return rightStickYToSigned(xboxController_->xboxNotif.joyRVert);
}

uint16_t Controller::getLeftTrigger() const {
    if (!xboxController_ || !isConnected_) return 0;
    return xboxController_->xboxNotif.trigLT;
}

uint16_t Controller::getRightTrigger() const {
    if (!xboxController_ || !isConnected_) return 0;
    return xboxController_->xboxNotif.trigRT;
}

bool Controller::getButtonA() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnA;
}

bool Controller::getButtonB() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnB;
}

bool Controller::getButtonX() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnX;
}

bool Controller::getButtonY() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnY;
}

bool Controller::getButtonLB() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnLB;
}

bool Controller::getButtonRB() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnRB;
}

bool Controller::getButtonXbox() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnXbox;
}

bool Controller::getButtonStart() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnStart;
}

bool Controller::getButtonSelect() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnSelect;
}

bool Controller::getButtonLS() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnLS;
}

bool Controller::getButtonRS() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnRS;
}

bool Controller::getButtonDirUp() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnDirUp;
}

bool Controller::getButtonDirDown() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnDirDown;
}

bool Controller::getButtonDirLeft() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnDirLeft;
}

bool Controller::getButtonDirRight() const {
    if (!xboxController_ || !isConnected_) return false;
    return xboxController_->xboxNotif.btnDirRight;
}

void Controller::requestEmergencyStop() {
    emergencyStopRequested_ = true;
}

bool Controller::isEmergencyStopRequested() {
    return emergencyStopRequested_;
}

void Controller::clearEmergencyStop() {
    emergencyStopRequested_ = false;
}

void Controller::startConnection() {
    if (xboxController_) {
        xboxController_->begin();
        isConnecting_ = true;
        LOG_INFO("Starting Xbox controller connection...");
    }
}

void Controller::disconnect() {
    if (xboxController_) {
        isConnected_ = false;
        isConnecting_ = false;
        LOG_INFO("Xbox controller disconnected");
    }
}

void Controller::updateMotionCommand() {
    MotionCommand cmd;
    cmd.valid = isConnected();
    cmd.forwardBackward = 0;
    cmd.leftRight = 0;
    cmd.turn = 0;
    cmd.rtPressed = (getRightTrigger() > 0x80);

    if (!cmd.valid) {
        g_motionCommand = cmd;
        return;
    }

    // RB 键切换速度模式：检测上升沿（按下瞬间触发）
    bool currentRbState = getButtonRB();
    if (currentRbState && !previousRbState_) {
        rtModeIsFast_ = !rtModeIsFast_;
        LOG_INFO("RT speed mode changed: %s", rtModeIsFast_ ? "FAST" : "SLOW");
    }
    previousRbState_ = currentRbState;

    int16_t ryRaw = getRightStickY();
    int16_t rxRaw = getRightStickX();
    int16_t lxRaw = getLeftStickX();

    // 调试：打印原始摇杆值
    static int debugCounter = 0;
    if ((ryRaw != 0 || rxRaw != 0 || lxRaw != 0) && debugCounter++ % 5 == 0) {
        LOG_INFO("Raw - ry: %d, rx: %d, lx: %d", ryRaw, rxRaw, lxRaw);
    }

    // 右摇杆控制移动（前后/左右）
    // 将16位有符号整数归一化到-1.0 ~ 1.0范围
    
    // 归一化函数：将int16转换为-1.0~1.0，溢出时保持边缘
    auto normalizeAxis = [](int16_t value) -> float {
        if (value > 0) {
            // 正数归一化到 0.0 ~ 1.0
            // 最大预期范围是0~32767
            if (value >= 32767) return 1.0f;
            return (float)value / 32767.0f;
        } else if (value < 0) {
            // 负数归一化到 -1.0 ~ 0.0
            // 最小预期范围是-32768
            if (value <= -32768) return -1.0f;
            return (float)value / 32767.0f;
        } else {
            return 0.0f;
        }
    };
    
    // 归一化处理
    float ryNorm = normalizeAxis(ryRaw);
    float rxNorm = normalizeAxis(rxRaw);
    float lxNorm = normalizeAxis(lxRaw);
    
    // 将死区阈值也归一化
    float deadzoneNorm = (float)kDeadzoneThreshold / 32767.0f;
    
    if (fabs(ryNorm) > deadzoneNorm || fabs(rxNorm) > deadzoneNorm) {
        float absRyNorm = fabs(ryNorm);
        float absRxNorm = fabs(rxNorm);
        
        if (absRyNorm >= absRxNorm) {
            // 主要方向是前后
            cmd.forwardBackward = (ryNorm < 0) ? 1 : -1;
        } else {
            // 主要方向是左右
            cmd.leftRight = (rxNorm > 0) ? 1 : -1;
        }
    }

    // 左摇杆控制转向
    // 使用归一化后的值
    if (fabs(lxNorm) > deadzoneNorm) {
        cmd.turn = (lxNorm > 0) ? 1 : -1;
    }

    // 速度控制 - 只根据RT按键和当前模式决定速度等级
    // 默认模式(rtModeIsFast_=true)：按下RT=极速(1.0x)，不按RT=中等速度(0.5x)
    // 慢速模式(rtModeIsFast_=false)：按下RT=慢速(0.25x)，不按RT=中等速度(0.5x)
    if (cmd.rtPressed) {
        cmd.speedLevel = rtModeIsFast_ ? hexapod::SPEED_FAST : hexapod::SPEED_SLOWEST;
    } else {
        cmd.speedLevel = hexapod::SPEED_MEDIUM;
    }

    g_motionCommand = cmd;
}

int16_t Controller::applyDeadzone(int16_t raw) const {
    if (raw > -kDeadzoneThreshold && raw < kDeadzoneThreshold) {
        return 0;
    }
    return raw;
}

float Controller::normalizeAxis(int16_t raw) const {
    if (raw == 0) return 0.0f;
    return static_cast<float>(raw) / 32767.0f;
}

hexapod::SpeedLevel Controller::calculateSpeedLevel(float magnitude, bool rtPressed) const {
    if (rtPressed) {
        return hexapod::SPEED_FAST;
    }

    if (magnitude > 0.8f) {
        return hexapod::SPEED_MEDIUM;
    } else if (magnitude > 0.5f) {
        return hexapod::SPEED_SLOW;
    } else if (magnitude > 0.3f) {
        return hexapod::SPEED_SLOWEST;
    }

    return hexapod::SPEED_SLOWEST;
}

int16_t Controller::leftStickXToSigned(int16_t raw) const {
    return raw - 32767;
}

int16_t Controller::leftStickYToSigned(int16_t raw) const {
    return raw - 32767;
}

int16_t Controller::rightStickXToSigned(int16_t raw) const {
    return raw - 32767;
}

int16_t Controller::rightStickYToSigned(int16_t raw) const {
    return raw - 32767;
}

const MotionCommand& getMotionCommand() {
    return g_motionCommand;
}

}  // namespace gamepad
