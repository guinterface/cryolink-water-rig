#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cli=<scratch>/cryolink_arduino/bin/arduino-cli
cfg=esp32/arduino-cli.yaml
"$cli" core update-index --config-file "$cfg"
"$cli" core install esp32:esp32@3.3.2 --config-file "$cfg"
for lib in 'Adafruit PWM Servo Driver Library@3.0.2' 'OneWire@2.3.8' 'DallasTemperature@4.0.5' 'HX711 Arduino Library@0.7.5' 'Adafruit MPRLS Library@1.2.2' 'Adafruit BusIO@1.17.4' 'Adafruit Unified Sensor@1.1.15'; do
  "$cli" lib install "$lib" --config-file "$cfg"
done
"$cli" compile --config-file "$cfg" --fqbn esp32:esp32:featheresp32 \
  --build-path <scratch>/cryolink_arduino/build esp32/cryolink_mcu
