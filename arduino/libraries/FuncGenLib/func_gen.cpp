/*
  func_gen.cpp - Library for generating functional output
  Created by Craig Wm. Versek, 2012-08-21
  Released into the public domain.
*/
#if ARDUINO >= 100
  #include "Arduino.h"
#else
  #include "WProgram.h"
#endif

#include "func_gen.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

FunctionGenerator::FunctionGenerator(){
    setFuncOff(); 
    resetTime();
}

void FunctionGenerator::resetTime(){
    _t0_microseconds = micros();
}

void FunctionGenerator::setFuncOff(){
    _func = OFF;
    _func_freq  = 0.0;
    _func_amp   = 0.0;
    _func_phase = 0.0; 
    resetTime();
}

void FunctionGenerator::setFuncSin(double freq, double amp){
    _func = SIN;
    _func_freq = freq;
    _func_amp  = amp;
    _func_phase = 0.0;
    resetTime();
}

void FunctionGenerator::setFuncSin(double freq, double amp, double phase){
    _func = SIN;
    _func_freq  = freq;
    _func_amp   = amp;
    _func_phase = phase;
    resetTime();
}

double FunctionGenerator::compute(){
    unsigned long t_microseconds = micros() - _t0_microseconds; 
    switch (_func)
    {
        case OFF:
            return 0.0;        
        case SIN:
            return _func_amp*sin(2.0*M_PI*_func_freq*1e-6*t_microseconds + _func_phase);
    }
}
