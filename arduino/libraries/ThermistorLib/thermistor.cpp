/*
  thermistor.cpp - Library for measuring temperature with thermistors
  Created by Craig Wm. Versek, 2012-08-12
  Modified by Matthew Bockmann
  Released into the public domain.
*/
#include "thermistor.h"
#include <Arduino.h>
#include <math.h>


Thermistor::Thermistor(double A, double B, double C, double R_25C, double R_std){
    _A = A;
    _B = B;
    _C = C;
    _R_25C = R_25C;
    _R_std = R_std;
    _analogSensePin = A0;
}

void Thermistor::begin(int analogSensePin ){
    _analogSensePin = analogSensePin;
    pinMode(analogSensePin, INPUT);
}

double Thermistor::readVoltage(){
    return analogRead(_analogSensePin)*VOLTAGE_REF/MAX_10BIT;
}

double Thermistor::readResistance(){
    double V = readVoltage();
    return V*_R_std/(VOLTAGE_REF - V);
}    

double Thermistor::readTemperature(){
    double R = readResistance();
    double logR = log10(R/_R_25C);
    double T_kelvin = 1000.0/(_A + _B*logR + _C*pow(logR,2));
    //convert to Celcius
    return T_kelvin + T_ABS;
}
