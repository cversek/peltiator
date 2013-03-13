/*
  L298N.cpp - Library for interacting with an L298N
              Dual Full Bridge Driver
  Created by Craig Wm. Versek, 2012-08-10
  Released into the public domain.
 */

#include <Arduino.h>
#include <L298N.h>
#include <math.h>

#define MAX_DELAY_MIRCOSECONDS 16383

L298NClass::L298NClass(){
    _chanA_active = false;
    _chanB_active = false;
}

void L298NClass::configChannelA(int input1Pin,
                                int input2Pin,
                                int enableAPin
                               ){
    _input1Pin = input1Pin;
    _input2Pin = input2Pin;
    _enableAPin = enableAPin;
    _chanA_active = true;
}

void L298NClass::configChannelB(int input3Pin,
                                int input4Pin,
                                int enableBPin
                               ){
    _input3Pin = input3Pin;
    _input4Pin = input4Pin;
    _enableBPin = enableBPin;
    _chanB_active = true;
}

void L298NClass::begin(){
    if(_chanA_active){
        pinMode( _input1Pin, OUTPUT );
        pinMode( _input2Pin, OUTPUT );
        pinMode( _enableAPin, OUTPUT );
        digitalWrite( _input1Pin, LOW );
        digitalWrite( _input2Pin, LOW );
        digitalWrite( _enableAPin, HIGH );
    }
    if(_chanB_active){
        pinMode( _input3Pin, OUTPUT );
        pinMode( _input4Pin, OUTPUT );
        pinMode( _enableBPin, OUTPUT );
        digitalWrite( _input3Pin, LOW );
        digitalWrite( _input4Pin, LOW );
        digitalWrite( _enableBPin, HIGH );
    }
}

void L298NClass::drive(double chanA_pwm_fract, double chanB_pwm_fract, double drive_period)
{
    chanA_pwm_fract = constrain(chanA_pwm_fract, -1.0, 1.0);
    chanB_pwm_fract = constrain(chanB_pwm_fract, -1.0, 1.0);    
    double onTimeA = drive_period*abs(chanA_pwm_fract);
    double onTimeB = drive_period*abs(chanB_pwm_fract);
    double t1 = min(onTimeA,onTimeB);
    double t2 = onTimeB - onTimeA;
    double t3 = drive_period - max(onTimeA, onTimeB);
    //ON PULSE
    if(_chanA_active){
        if(chanA_pwm_fract < 0){ //negative pulse
            
            // turn off positive current first
            digitalWrite( _input1Pin, LOW );
            //then turn on negative current for ON pulse
            digitalWrite( _input2Pin, HIGH );
        }
        else{                      //positive pulse
            // turn off negative current first
            digitalWrite( _input2Pin, LOW );
            //then turn on positive current for ON pulse
            digitalWrite( _input1Pin, HIGH );
        }
    }
    if(_chanB_active){
        if(chanB_pwm_fract < 0){ //negative pulse
            
            // turn off positive current first
            digitalWrite( _input3Pin, LOW );
            //then turn on negative current for ON pulse
            digitalWrite( _input4Pin, HIGH );
        }
        else{                      //positive pulse
            // turn off negative current first
            digitalWrite( _input4Pin, LOW );
            //then turn on positive current for ON pulse
            digitalWrite( _input3Pin, HIGH );
        }
    }
    delayReal(t1);
    //TURN MIN OFF
    if(t2 > 0 && _chanA_active){
        if(chanA_pwm_fract < 0){ //negative pulse
            digitalWrite( _input2Pin, LOW );
        }
        else{                      //positive pulse
            digitalWrite( _input1Pin, LOW );
        }
    }
    else if(_chanB_active){
        if(chanB_pwm_fract < 0){ //negative pulse
            digitalWrite( _input4Pin, LOW );
        }
        else{                      //positive pulse
            digitalWrite( _input3Pin, LOW );
        }
    }
    delayReal(abs(t2));
   //TURN MAX OFF
    if(t2 > 0 && _chanB_active){
        if(chanB_pwm_fract < 0){ //negative pulse
            digitalWrite( _input4Pin, LOW );
        }
        else{                      //positive pulse
            digitalWrite( _input3Pin, LOW );
        }
    }
    else if(_chanA_active){
        if(chanA_pwm_fract < 0){ //negative pulse
            digitalWrite( _input2Pin, LOW );
        }
        else{                      //positive pulse
            digitalWrite( _input1Pin, LOW );
        }
    }
    //WAIT UNTIL NEXT PERIOD
    delayReal(t3);
}

//---HELPER FUNCTIONS-----------------------------------------------------------
void delayReal(double t){
    t *= 1e6;
    if (t > MAX_DELAY_MIRCOSECONDS)
    {
        delay(t*1e-3);
    }
    else
    {
        if (t < 3.0) {t=3.0;}
        delayMicroseconds(t);  //warning doesn't work with t < 3
    }
}
