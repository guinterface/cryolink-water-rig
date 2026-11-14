#include <Arduino.h>
#include <atomic>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <HX711.h>
#include <Adafruit_MPRLS.h>
#include "Calibration.h"
#include "Safety.h"

Adafruit_PWMServoDriver pwm(0x40);
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature thermometers(&oneWire);
HX711 scale;
Adafruit_MPRLS pressure(-1,-1);
Safety safety;
struct Samples { float wall=0, inlet=0, mass=0, p=0; uint32_t stamp=0; bool ok=false; };
Samples samples;
portMUX_TYPE sampleMux=portMUX_INITIALIZER_UNLOCKED;
std::atomic<bool> pwmOK{false};
bool mechanismEnabled=false;
bool actuatorFault=false; // latched on I2C PWM write failure; reboot after inspection
char input[256]; size_t used=0; bool dropping=false;
uint32_t statusAt=0, statusSeq=0;
float previousAngle[4]={-999,-999,-999,-999};

// Sensors are on another task: a missing sensor never blocks the safety loop.
// Wire transaction timeout bounded; Dallas conversions asynchronous; HX read only if ready.
void sensorTask(void *) {
  Wire.begin(I2C_SDA,I2C_SCL); Wire.setTimeOut(20);
  bool foundPWM=pwm.begin();
  if(foundPWM) { pwm.setOscillatorFrequency(PCA_OSC_HZ); pwm.setPWMFreq(50); }
  pwmOK=foundPWM;
  // Initialization completes before main loop is allowed to use the bus.
  thermometers.begin(); thermometers.setResolution(10); thermometers.setWaitForConversion(false);
  scale.begin(HX_DOUT,HX_SCK);
  bool pressureOK=pressure.begin(0x18,&Wire);
  thermometers.requestTemperatures();
  uint32_t convertAt=millis(), massAt=0;
  Samples local;
  for(;;) {
    uint32_t now=millis();
    if(scale.is_ready()) { local.mass=(scale.read()-HX_ZERO_COUNTS)/HX_COUNTS_PER_GRAM; massAt=now; }
    if(uint32_t(now-convertAt)>=200) {
      local.wall=thermometers.getTempC(WALL_ROM);
      local.inlet=thermometers.getTempC(INLET_ROM);
      thermometers.requestTemperatures(); convertAt=now;
      // MPRLS hPa -> kPa absolute; air-filled tee must stay dry.
      local.p=pressureOK?pressure.readPressure()/10.f:NAN;
      local.stamp=millis();
      local.ok=pressureOK && isfinite(local.p) && local.p>0 && local.p<200 &&
        local.wall>=-55 && local.wall<=125 && local.inlet>=-55 && local.inlet<=125 &&
        uint32_t(now-massAt)<500 && massAt!=0;
      portENTER_CRITICAL(&sampleMux); samples=local; portEXIT_CRITICAL(&sampleMux);
    }
    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

// PCA and MPRLS share Wire: Arduino ESP32 Wire serializes individual transactions.
// Servo writes occur on safety task, never on sensor task after initialization.
void angle(int channel, float degrees) {
  degrees=constrain(degrees,SERVO_MIN_DEG,SERVO_MAX_DEG);
  if(previousAngle[channel]==degrees || !pwmOK) return;
  float us=SERVO_MIN_US+(SERVO_MAX_US-SERVO_MIN_US)*degrees/180.f;
  if(pwm.setPWM(channel,0,uint16_t(us*4096.f/20000.f))==0) previousAngle[channel]=degrees;
  else actuatorFault=true;
}
void actuate() {
  // Feed first: isolation precedes any latch opening or carriage motion in this tick.
  angle(FEED_CHANNEL,safety.feed?FEED_OPEN_DEG:FEED_CLOSED_DEG);
  angle(DRAIN_CHANNEL,safety.drain?DRAIN_OPEN_DEG:DRAIN_CLOSED_DEG);
  // At boot, leave carriage/latch PWM disabled until a valid, calibrated command.
  // This prevents an uncommanded home stroke against already-closed hooks.
  if(!mechanismEnabled && safety.safe) return;
  mechanismEnabled=true;
  // Geometric crank mapping: x = r*(1-cos(theta)), not linear travel vs angle.
  float x=constrain(safety.carriage,CARRIAGE_MIN_MM,CARRIAGE_MAX_MM);
  float phase=acosf(1.f-2.f*x/CARRIAGE_MAX_MM)/PI;
  angle(CARRIAGE_CHANNEL,CARRIAGE_MATED_DEG+phase*(CARRIAGE_HOME_DEG-CARRIAGE_MATED_DEG));
  angle(LATCH_CHANNEL,safety.latchCmd?LATCH_CLOSED_DEG:LATCH_OPEN_DEG);
}
void setup() {
  Serial.setTxBufferSize(512);
  Serial.begin(115200);
  pinMode(SEAT_PIN,INPUT_PULLUP); pinMode(LATCH_PIN,INPUT_PULLUP); pinMode(HOME_PIN,INPUT_PULLUP);
  xTaskCreatePinnedToCore(sensorTask,"sensors",6144,nullptr,1,nullptr,0);
}
void loop() {
  uint32_t now=millis();
  // Bound serial work per tick; garbage flood cannot starve watchdog.
  for(int n=0;n<256&&Serial.available();++n) {
    char c=Serial.read();
    if(c=='\n') {
      if(!dropping) { input[used]=0; Setpoint sp; if(parseSP(input,sp)) safety.accept(sp,now); }
      used=0; dropping=false;
    } else if(!dropping) {
      if(c==0 || used>=sizeof(input)-1) { used=0; dropping=true; }
      else input[used++]=c;
    }
  }
  bool seat=digitalRead(SEAT_PIN)==LOW, latch=digitalRead(LATCH_PIN)==LOW, home=digitalRead(HOME_PIN)==LOW;
  Samples s; portENTER_CRITICAL(&sampleMux); s=samples; portEXIT_CRITICAL(&sampleMux);
  if(!mechanismEnabled) { safety.carriage=seat?0.f:36.f; safety.latchCmd=latch; }
  safety.tick(now,seat,latch,home,!(latch&&!seat)&&!(home&&seat)&&s.ok&&uint32_t(now-s.stamp)<500&&pwmOK&&!actuatorFault,RIG_CALIBRATED);
  actuate();
  if(uint32_t(now-statusAt)>=100 && Serial.availableForWrite()>=240) {
    statusAt=now; char body[240],frame[256];
    // Invalid numeric values are transmitted as zero with SENSOR fault, never a valid reading.
    snprintf(body,sizeof(body),"ST %lu seat=%d latch=%d home=%d Twall=%.3f Tin=%.3f m=%.3f p=%.4f feed=%d drain=%d safe=%d fault=%s",
      (unsigned long)statusSeq++,seat,latch,home,isfinite(s.wall)?s.wall:0.,isfinite(s.inlet)?s.inlet:0.,
      isfinite(s.mass)?s.mass:0.,isfinite(s.p)?s.p:0.,safety.feed,safety.drain,safety.safe,safety.fault);
    snprintf(frame,sizeof(frame),"%s*%04X\n",body,crc16(body,strlen(body))); Serial.print(frame);
  }
  delay(2);
}
