/*
  ThermistorTest.ino - Arduino Library Example sketch for the Thermistor class
  Created by Craig Wm. Versek, 2012-08-12
  Modified by Matthew Bockmann
  Released into the public domain.
*/

#include <thermistor.h>
// Calibration coeffs for RSBR-302J-Z50 Teflon-Coated 3k Thermistor
#define A 3.3501
#define B 0.5899
#define C 0.0104
#define R_25C 3000.0 /*ohms*/
#define R_STANDARD 3003.0 /*ohms*/

Thermistor firstThermistor(A,B,C,R_25C,R_STANDARD);

void setup() {
   Serial.begin(9600);
   firstThermistor.begin(0);
}

void loop() {
    double V = firstThermistor.readVoltage();
    double R = firstThermistor.readResistance();
    double T = firstThermistor.readTempurature();
    Serial.println("---");
    Serial.print("voltage: ");
    Serial.println(V);
    Serial.print("resistance: ");
    Serial.println(R);
    Serial.print("temperature: ");
    Serial.println(T);
    delay(1000);
}
