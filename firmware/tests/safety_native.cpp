#include "../esp32/cryolink_mcu/Safety.h"
#include <assert.h>
#include <iostream>
int main(int argc, char **) {
  if(argc>1) { // Python corpus driver: parse one wire line per input line.
    char line[1024];
    while(std::cin.getline(line,sizeof(line))) { Setpoint s; std::cout<<parseSP(line,s)<<"\n"; }
    return 0;
  }
  Safety m; Setpoint c; c.carriage=0; c.latch=true; c.feed=true; c.drain=false; c.seq=1; c.hb=1;
  assert(m.accept(c,10)); m.tick(10,false,true,false); assert(!m.feed && !strcmp(m.fault,"INTERLOCK"));
  c.seq++;c.hb++;assert(m.accept(c,20)); m.tick(20,true,false,false);assert(!m.feed&&!strcmp(m.fault,"INTERLOCK"));
  c.seq++;c.hb++;assert(m.accept(c,30)); m.tick(30,true,true,false);assert(m.feed&&!m.safe);
  // Latch opening while requested feed remains open must be rejected.
  c.seq++;c.hb++;c.latch=false;assert(m.accept(c,40));m.tick(40,true,true,false);
  assert(m.latchCmd&&!strcmp(m.fault,"LATCH_FEED"));
  // Switch loss isolates even without another command.
  m.tick(41,false,true,false);assert(!m.feed);
  // Stale hb cannot be kept alive by fresh SP sequence numbers.
  for(unsigned t=100;t<1040;t+=100) { c.seq++;assert(m.accept(c,t));m.tick(t,true,true,false); }
  m.tick(1040,true,true,false);assert(m.safe&&!m.feed&&m.drain);
  // Replay and invalid range do not reset timers.
  assert(!m.accept(c,1050));
  Safety stuck; c={}; c.carriage=0;c.latch=true;c.seq=1;c.hb=1;
  assert(stuck.accept(c,0));stuck.tick(0,false,false,false);
  stuck.tick(199,false,false,false);assert(strcmp(stuck.fault,"STUCK"));
  stuck.tick(200,false,false,false);assert(!strcmp(stuck.fault,"STUCK")&&!stuck.feed&&stuck.drain);
  Safety retract; c.carriage=0;assert(retract.accept(c,0));retract.tick(0,true,true,false);
  c.seq++;c.hb++;c.carriage=36;assert(retract.accept(c,10));retract.tick(10,true,true,false);
  assert(retract.carriage==0&&!strcmp(retract.fault,"RETRACT"));
  retract.tick(11,true,true,false,false);assert(retract.safe&&!retract.feed&&retract.drain);
  retract.tick(12,true,true,false,true,false);
  assert(retract.safe&&!retract.feed&&retract.drain&&!strcmp(retract.fault,"CALIBRATION"));
  // millis rollover must not defeat watchdog.
  Safety wrap;c.seq=0xFFFFFFFF;c.hb=0xFFFFFFFF;c.feed=false;
  assert(wrap.accept(c,0xFFFFFF00));c.seq=0;c.hb=0;assert(wrap.accept(c,0xFFFFFF80));
  wrap.tick(0x00000368,false,false,true);assert(wrap.safe);
  std::cout<<"native safety: interlocks, latch, retract, mismatch 200ms, heartbeat, sensor fail, rollover PASS\n";
}
