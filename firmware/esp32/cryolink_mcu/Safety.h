#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Protocol ASSUMPTIONS are shared with rig_bridge/protocol.py; no heap allocation.
struct Setpoint {
  uint32_t seq = 0, hb = 0;
  float carriage = 36;
  bool latch = false, feed = false, drain = true;
};
inline uint16_t crc16(const char *s, size_t n) {
  uint16_t crc = 0xFFFF;
  for (size_t i=0; i<n; ++i) {
    crc ^= uint16_t(uint8_t(s[i])) << 8;
    for (int b=0; b<8; ++b) crc = (crc & 0x8000) ? (crc << 1)^0x1021 : crc << 1;
  }
  return crc;
}
inline bool newer(uint32_t a, uint32_t b) { uint32_t d = a-b; return d && d < 0x80000000UL; }
inline bool uint32parse(const char *s, uint32_t &v) {
  if (!*s) return false;
  uint64_t n=0;
  for (; *s; ++s) { if (*s<'0' || *s>'9') return false; n=n*10+(*s-'0'); if(n>0xFFFFFFFFULL) return false; }
  v=uint32_t(n); return true;
}
inline bool parseSP(char *line, Setpoint &sp) {
  size_t len=strlen(line);
  if (len>255 || len<10) return false;
  char *star=strchr(line, '*');
  if (!star || strlen(star+1)!=4) return false;
  for(char *c=star+1; *c; ++c) if(!((*c>='0'&&*c<='9')||(*c>='a'&&*c<='f')||(*c>='A'&&*c<='F'))) return false;
  if (crc16(line, star-line)!=strtoul(star+1,nullptr,16)) return false;
  *star=0;
  char *save=nullptr, *tok=strtok_r(line," ",&save);
  if (!tok || strcmp(tok,"SP")) return false;
  tok=strtok_r(nullptr," ",&save);
  if (!tok || !uint32parse(tok,sp.seq)) return false;
  unsigned mask=0;
  while((tok=strtok_r(nullptr," ",&save))) {
    char *eq=strchr(tok,'='); if(!eq) return false; *eq++=0;
    unsigned bit=0;
    if(!strcmp(tok,"carriage")) {
      bit=1; char *end=nullptr; sp.carriage=strtof(eq,&end);
      if(!*eq || *end || !isfinite(sp.carriage) || sp.carriage<0 || sp.carriage>36) return false;
    } else if(!strcmp(tok,"latch")) {
      bit=2; if(!strcmp(eq,"closed")) sp.latch=true; else if(!strcmp(eq,"open")) sp.latch=false; else return false;
    } else if(!strcmp(tok,"feed") || !strcmp(tok,"drain")) {
      if(strcmp(eq,"0") && strcmp(eq,"1")) return false;
      if(!strcmp(tok,"feed")) { bit=4; sp.feed=*eq=='1'; } else { bit=8; sp.drain=*eq=='1'; }
    } else if(!strcmp(tok,"hb")) { bit=16; if(!uint32parse(eq,sp.hb)) return false; }
    else return false;
    if(mask&bit) return false;
    mask|=bit;
  }
  return mask==31;
}

struct Safety {
  Setpoint cmd;
  uint32_t lastSP=0, lastHB=0, seq=0, hb=0, mismatchAt=0;
  bool haveSP=false, haveHB=false, mismatchActive=false;
  bool feed=false, drain=true, latchCmd=false, safe=true;
  float carriage=36;
  const char *fault="WATCHDOG";
  bool accept(const Setpoint &s, uint32_t now) {
    if(haveSP && !newer(s.seq,seq)) return false;
    cmd=s; seq=s.seq; haveSP=true; lastSP=now;
    if(!haveHB || newer(s.hb,hb)) { hb=s.hb; lastHB=now; haveHB=true; }
    return true;
  }
  void tick(uint32_t now, bool seat, bool latch, bool home, bool sensorsOK=true, bool calibrated=true) {
    safe=!haveSP || !haveHB || uint32_t(now-lastSP)>=1000 || uint32_t(now-lastHB)>=1000;
    fault=safe?"WATCHDOG":"NONE";
    feed=cmd.feed&&!safe; drain=cmd.drain||safe;
    if(feed && !(seat&&latch)) { feed=false; fault="INTERLOCK"; }
    if(!safe) {
      if(!cmd.latch && feed) fault="LATCH_FEED";
      else latchCmd=cmd.latch;
      if(cmd.carriage>carriage && (latch || latchCmd)) fault="RETRACT";
      else carriage=cmd.carriage;
    }
    bool mismatch=latchCmd!=latch || (carriage<=.5f&&!seat) || (carriage>=35.5f&&!home);
    if(mismatch && !mismatchActive) { mismatchAt=now; mismatchActive=true; }
    if(!mismatch) mismatchActive=false;
    if(mismatchActive && uint32_t(now-mismatchAt)>=200 && !safe) {
      if(!strcmp(fault,"NONE")) fault="STUCK";
      feed=false; drain=true;
    }
    if(!sensorsOK || !calibrated) {
      safe=true; feed=false; drain=true; fault=!calibrated?"CALIBRATION":"SENSOR";
    }
  }
};
