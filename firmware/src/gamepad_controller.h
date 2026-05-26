#pragma once

#include <Arduino.h>
#include <cstdint>

#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

#include <XboxSeriesXControllerESP32_asukiaaa.hpp>
#include "config.h"

namespace gamepad {

constexpr uint16_t XboxControllerTimeoutMs = 10000;

class Controller {
public:
    static Controller& instance();

    void begin(const char* xboxMacAddress);
    void onLoopTick();

    bool isConnected() const;
    bool isConnecting() const;

    int16_t getLeftStickX() const;
    int16_t getLeftStickY() const;
    int16_t getRightStickX() const;
    int16_t getRightStickY() const;
    uint16_t getLeftTrigger() const;
    uint16_t getRightTrigger() const;

    bool getButtonA() const;
    bool getButtonB() const;
    bool getButtonX() const;
    bool getButtonY() const;
    bool getButtonLB() const;
    bool getButtonRB() const;
    bool getButtonXbox() const;
    bool getButtonStart() const;
    bool getButtonSelect() const;
    bool getButtonLS() const;
    bool getButtonRS() const;
    bool getButtonDirUp() const;
    bool getButtonDirDown() const;
    bool getButtonDirLeft() const;
    bool getButtonDirRight() const;

    void requestEmergencyStop();
    bool isEmergencyStopRequested();
    void clearEmergencyStop();

    void startConnection();
    void disconnect();

    bool isGimbalModeActive() const;
    bool isSingleLegTriggered() const;

    float getGimbalPanNormalized() const;
    float getGimbalTiltNormalized() const;

private:
    Controller() = default;
    Controller(const Controller&) = delete;
    Controller& operator=(const Controller&) = delete;

    void updateMotionCommand();
    int16_t applyDeadzone(int16_t raw) const;
    float normalizeAxis(int16_t raw) const;
    hexapod::SpeedLevel calculateSpeedLevel(float magnitude, bool rtPressed) const;

    int16_t leftStickXToSigned(int16_t raw) const;
    int16_t leftStickYToSigned(int16_t raw) const;
    int16_t rightStickXToSigned(int16_t raw) const;
    int16_t rightStickYToSigned(int16_t raw) const;

    XboxSeriesXControllerESP32_asukiaaa::Core* xboxController_;
    bool isConnected_;
    bool isConnecting_;
    bool emergencyStopRequested_;
    mutable SemaphoreHandle_t mutex_;
    static constexpr int16_t kDeadzoneThreshold = 5000;
    
    // 速度模式切换
    bool rtModeIsFast_ = true;
    bool previousRbState_ = false;

    // 云台控制模式（LT触发）
    bool gimbalModeActive_ = false;

    // 单腿控制模式切换（LB触发，上升沿检测）
    bool previousLbState_ = false;
    bool singleLegTriggered_ = false;
};

Controller& controller();

struct MotionCommand {
    bool valid;
    int8_t forwardBackward;
    int8_t leftRight;
    int8_t turn;
    hexapod::SpeedLevel speedLevel;
    bool rtPressed;
};

const MotionCommand& getMotionCommand();

}  // namespace gamepad
