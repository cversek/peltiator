/*
  FuncGenTest.ino - Arduino Library Example sketch for the Thermistor class
  Created by Craig Wm. Versek, 2012-08-12
  Modified by Matthew Bockmann
  Released into the public domain.
*/

#include <func_gen.h>

FunctionGenerator FG;

void setup() {
   Serial.begin(9600);
   FG.setFuncSin(0.01,1.0);
   FG.resetTime();
}

void loop(){
    Serial.println(FG.compute());
    delay(1000);
}
