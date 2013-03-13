/*
  func_gen.h - Library for generating functional output
  Created by Craig Wm. Versek, 2012-08-21
  Released into the public domain.
*/

#ifndef _FUNC_GEN_H_INCLUDED
#define _FUNC_GEN_H_INCLUDED
enum FunctionType {OFF,SIN,SQUARE,TRIANGLE,SAWTOOTH};

class FunctionGenerator{
public:
    FunctionGenerator();
    void resetTime();
    void setFuncOff();
    void setFuncSin(double freq, double amp);
    void setFuncSin(double freq, double amp, double phase);
    double compute();
private:
    unsigned long _t0_microseconds;
    double _samp_freq;
    double _func_freq;
    double _func_amp;
    double _func_phase;
    FunctionType _func;
};

#endif //_FUNC_GEN_H_INCLUDED
