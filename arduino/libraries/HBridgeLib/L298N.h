/*
  L298N.h - Library for interacting with an L298N
              Dual Full Bridge Driver
  Created by Craig Wm. Versek, 2012-08-10
  Released into the public domain.
 */

#ifndef _L298N_H_INCLUDED
#define _L298N_H_INCLUDED

class L298NClass{
public:
  L298NClass();
  //Configuration methods
  void configChannelA(int input1Pin,
                      int input2Pin,
                      int enableAPin
                     );
  void configChannelB(int input3Pin,
                      int input4Pin,
                      int enableBPin
                     );
  void begin(); // Default
  //void end();
  //Functionality methods
  void drive(double chanA_pwm_fract, 
             double chanB_pwm_fract, 
             double drive_period);

private:
  int _input1Pin;
  int _input2Pin;
  int _enableAPin;
  int _input3Pin;
  int _input4Pin;
  int _enableBPin;
  bool _chanA_active;
  bool _chanB_active;
};

// HELPER FUNCTIONS
void delayReal(double t);

#endif //_L298N_H_INCLUDED
