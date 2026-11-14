#pragma once
// ASSUMPTION: all provisional servo/PWM/scale values below require measured calibration.
// CALIBRATE: false until all endpoints, sensor ROMs, scale and switch trips verified dry.
constexpr bool RIG_CALIBRATED = false;
constexpr int SEAT_PIN=27, LATCH_PIN=33, HOME_PIN=14;
constexpr int ONE_WIRE_PIN=32, HX_DOUT=21, HX_SCK=25;
constexpr int I2C_SDA=23, I2C_SCL=22; // HUZZAH32 Feather pads, not generic ESP32 defaults
constexpr int CARRIAGE_CHANNEL=0, LATCH_CHANNEL=1, FEED_CHANNEL=2, DRAIN_CHANNEL=3;
// CALIBRATE: physical hard stops, horn phasing, and tubing closure. No sustained stall.
constexpr float SERVO_MIN_DEG=0, SERVO_MAX_DEG=180;
constexpr float CARRIAGE_MIN_MM=0, CARRIAGE_MAX_MM=36;
constexpr float CARRIAGE_MATED_DEG=170, CARRIAGE_HOME_DEG=10;
constexpr float LATCH_OPEN_DEG=50, LATCH_CLOSED_DEG=19;
constexpr float FEED_CLOSED_DEG=20, FEED_OPEN_DEG=80;
constexpr float DRAIN_CLOSED_DEG=20, DRAIN_OPEN_DEG=80;
constexpr float SERVO_MIN_US=500, SERVO_MAX_US=2500; // CALIBRATE actual safe PWM span
constexpr float PCA_OSC_HZ=25000000; // CALIBRATE oscillator for measured pulse widths
constexpr float HX_COUNTS_PER_GRAM=1000; // CALIBRATE signed scale from known weights
constexpr long HX_ZERO_COUNTS=0; // CALIBRATE unloaded receiver tare; never auto-tare filled receiver
// CALIBRATE: explicit ROM IDs avoid silently swapping wall and inlet on enumeration changes.
constexpr uint8_t WALL_ROM[8]={0,0,0,0,0,0,0,0};
constexpr uint8_t INLET_ROM[8]={0,0,0,0,0,0,0,0};
