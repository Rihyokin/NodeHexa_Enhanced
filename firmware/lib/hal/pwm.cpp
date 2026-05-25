
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#include "pwm.h"

namespace hexapod { namespace hal {

    PCA9685::PCA9685(int i2cAddress) : i2cAddress_(i2cAddress), obj_(nullptr) {
    }

    PCA9685::~PCA9685() {
        delete ((Adafruit_PWMServoDriver*)obj_);
    }

    void PCA9685::begin() {
        if (!obj_) {
            obj_ = (void*)new Adafruit_PWMServoDriver(i2cAddress_);
        }
        ((Adafruit_PWMServoDriver*)obj_)->begin();
    }

    void PCA9685::setPWMFreq(int freq) {
        if (!obj_) return;
        ((Adafruit_PWMServoDriver*)obj_)->setPWMFreq(freq);
    }

    void PCA9685::setPWM(int index, int on, int off) {
        if (!obj_) return;
        ((Adafruit_PWMServoDriver*)obj_)->setPWM(index, (uint16_t)on, (uint16_t)off);
    }

}}