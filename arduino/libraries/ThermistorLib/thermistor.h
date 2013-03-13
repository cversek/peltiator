/*
  thermistor.h - Library for measuring temperature with thermistors
  Created by Craig Wm. Versek, 2012-08-12
  Released into the public domain.
 */

#ifndef _THERMISTOR_H_INCLUDED
#define _THERMISTOR_H_INCLUDED
#define MAX_10BIT 1023     
#define VOLTAGE_REF 5.0        /* volts */
#define T_ABS -273.15         /* degrees Celsius */

class Thermistor{
public:
    Thermistor(double A, double B, double C, double R_25C, double R_std);
    void begin(int analogSensePin );
    double readVoltage();
    double readResistance();    
    double readTemperature();
private:
    double _A;
    double _B;
    double _C;
    double _R_25C;
    double _R_std;
    int _analogSensePin;
};

#endif //_THERMISTOR_H_INCLUDED
