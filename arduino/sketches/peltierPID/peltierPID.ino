/*******************************************************************************
  filename:     peltierPID
  desc:         Arduino firmware for dual peltier device control in 
                thermoelectric measurement apparatus
  author:       Craig Wm. Versek <cversek@physics.umass.edu>
  date_created: 2012-08-12
  license:      LGPL
*******************************************************************************/
//Standard Libraries
#include <math.h>
//3rd Party Libraries
#include <PID_v1.h>
#include <SerialCommand.h>
//1st Party Libraries
#include <L298N.h>
#include <thermistor.h>
#include <func_gen.h>

//------------------------------------------------------------------------------
//GLOBAL CONSTANTS

#define SERIAL_SPEED 115200

#define HBRIDGE_DRIVE_PERIOD 0.1
#define PID_SAMPLE_PERIOD    0.1


int control_mode_flags;
#define CONTROL_MODE_GRADIENT B00000001
#define CONTROL_MODE_PID_A    B00000010
#define CONTROL_MODE_PID_B    B00000100
#define CONTROL_MODE_FUNC_A   B00001000
#define CONTROL_MODE_FUNC_B   B00010000



//constants for RPGP-104M Thermistor A
#define THERM_A_A     3.3706
#define THERM_A_B     0.5694
#define THERM_A_C     4.30e-3
#define THERM_A_R_25C 100e3
#define THERM_A_R_STD 99.9e3
//#define THERM_A_R_STD 3.314e3

//constants for RPGP-104M Thermistor B
#define THERM_B_A     3.4009
#define THERM_B_B     0.5713
#define THERM_B_C     4.57e-3
#define THERM_B_R_25C 100e3
#define THERM_B_R_STD 100.7e3
//#define THERM_B_R_STD 3.310e3

//constants for RGLR-104F-3970 Thermistor C
#define THERM_C_A     3.3516
#define THERM_C_B     0.5840
#define THERM_C_C     1.89e-2
#define THERM_C_R_25C 100e3
#define THERM_C_R_STD 100.2e3
//#define THERM_C_R_STD 3.315e3

//PID controller
#define PID_OUTPUT_MIN -1.0
#define PID_OUTPUT_MAX  1.0

#define Kp 0.10
#define Ki 0.01
#define Kd 0.01

//------------------------------------------------------------------------------
//GLOBAL OBJECTS

//thermistors
Thermistor thermistorA(THERM_A_A, THERM_A_B, THERM_A_C, THERM_A_R_25C, THERM_A_R_STD);
Thermistor thermistorB(THERM_B_A, THERM_B_B, THERM_B_C, THERM_B_R_25C, THERM_B_R_STD);
Thermistor thermistorC(THERM_C_A, THERM_C_B, THERM_C_C, THERM_C_R_25C, THERM_C_R_STD);

//L298N H-Bridge
double chanA_output, chanB_output;
L298NClass HBridge;

//PID controller
double gradient_setpoint;
double chanA_PID_setpoint, chanA_PID_input, chanA_PID_output;
double chanB_PID_setpoint, chanB_PID_input, chanB_PID_output;
//Specify the links and initial tuning parameters
PID chanA_PID(&chanA_PID_input, &chanA_PID_output, &chanA_PID_setpoint, Kp, Ki, Kd, DIRECT);
PID chanB_PID(&chanB_PID_input, &chanB_PID_output, &chanB_PID_setpoint, Kp, Ki, Kd, DIRECT);

//Function Generation
double chanA_func_output, chanB_func_output;
FunctionGenerator chanA_FGen, chanB_FGen;

//SerialCommand parser
SerialCommand SCmd;
 
//------------------------------------------------------------------------------
//SETUP FUNCTION - main entry point, runs once each reset
void setup()
{
    Serial.begin(SERIAL_SPEED);
    // Setup callbacks for SerialCommand commands
    SCmd.addCommand("STATUS?",   getStatusCommand);
    SCmd.addCommand("TEMP_A",    setChanA_TemperatureTargetCommand);
    SCmd.addCommand("TEMP_B",    setChanB_TemperatureTargetCommand);
    SCmd.addCommand("GRAD"  ,    setGradientTargetCommand);
    SCmd.addCommand("PID_A",     setChanA_PIDModeCommand);
    SCmd.addCommand("PID_B",     setChanB_PIDModeCommand);
    SCmd.addCommand("FUNC_A",    setChanA_FuncCommand);
    SCmd.addCommand("FUNC_B",    setChanB_FuncCommand);
    SCmd.addCommand("FUNC_SYNC", funcSyncCommand);
    SCmd.addDefaultHandler(unrecognizedCommand);

    //configure the thermistor pins
    thermistorA.begin(A0);
    thermistorB.begin(A1);
    thermistorC.begin(A2);

    //initialize H-bridge controller
    HBridge.configChannelA(2, //input1Pin
                           3, //input2Pin
                           4  //enableAPin
                          );
    HBridge.configChannelB(5, //input3Pin
                           6, //input4Pin
                           7  //enableBPin
                          );
    HBridge.begin();

    //set up the PID controller
    setGradientTarget(0.0);     //safe initial condition
    chanA_PID.SetMode(AUTOMATIC);
    chanA_PID.SetOutputLimits(PID_OUTPUT_MIN, PID_OUTPUT_MAX);
    chanB_PID.SetMode(AUTOMATIC);
    chanB_PID.SetOutputLimits(PID_OUTPUT_MIN, PID_OUTPUT_MAX);
    chanA_PID.SetSampleTime(PID_SAMPLE_PERIOD*1000);
    chanB_PID.SetSampleTime(PID_SAMPLE_PERIOD*1000);

    //set up the function generators
    chanA_FGen.resetTime();
    chanB_FGen.resetTime();
}

//------------------------------------------------------------------------------
//LOOP FUNCTION - called by 'setup' runs continually
float T_A, T_B, T_C;
double drive_period;

unsigned int m0, m1;
double time_lost, time_correction;

void loop()
{
   
    m0 = micros();    
    //measure temperature
    T_A = thermistorA.readTemperature();
    T_B = thermistorB.readTemperature();
    T_C = thermistorC.readTemperature();
    
    //process serial commands
    SCmd.readSerial();

    //perform 'control mode' specific tasks
    if(control_mode_flags & CONTROL_MODE_GRADIENT)
    {
        chanA_PID_setpoint = T_C + gradient_setpoint/2.0;
        chanB_PID_setpoint = T_C - gradient_setpoint/2.0;
    }
    if(control_mode_flags & CONTROL_MODE_PID_A)
    {
        chanA_PID_input = T_A;
        chanA_PID.Compute(); //chanA_PID_output is updated
    } else{ 
        chanA_PID_output = 0.0;
    }
    if(control_mode_flags & CONTROL_MODE_PID_B)         
    {
        chanB_PID_input = T_B;
        chanB_PID.Compute(); //chanA_PID_output is updated
    } else{ 
        chanB_PID_output = 0.0;
    }
    if(control_mode_flags & CONTROL_MODE_FUNC_A)
    {
        chanA_func_output = chanA_FGen.compute();
    } else{ 
        chanA_func_output = 0.0;
    }
    if(control_mode_flags & CONTROL_MODE_FUNC_B)
    {
        chanB_func_output = chanB_FGen.compute();
    } else{ 
        chanB_func_output = 0.0;
    }
    //compensate for lost time
    m1 = micros();
    time_lost       = 1e-6*(m1 - m0);
    time_correction = 1.0 + time_lost/HBRIDGE_DRIVE_PERIOD;

    //compute and constrain total output
    chanA_output = constrain(time_correction*(chanA_PID_output + chanA_func_output),-1.0,1.0);
    chanB_output = constrain(time_correction*(chanB_PID_output + chanB_func_output),-1.0,1.0);
    //drive the system
    HBridge.drive(chanA_output, chanB_output, HBRIDGE_DRIVE_PERIOD - time_lost);
}

//------------------------------------------------------------------------------
//HELPER FUNCTIONS

void setChanA_PIDMode(int state)
{
    if (state > 0)
    {
        chanA_PID.SetMode(AUTOMATIC);
        control_mode_flags |= CONTROL_MODE_PID_A;
    }
    else
    {
        chanA_PID.SetMode(MANUAL);
        control_mode_flags &= ~CONTROL_MODE_PID_A;
    }
}

void setChanB_PIDMode(int state)
{
    if (state > 0)
    {
        chanB_PID.SetMode(AUTOMATIC);
        control_mode_flags |= CONTROL_MODE_PID_B;
    }
    else
    {
        chanB_PID.SetMode(MANUAL);
        control_mode_flags &= ~CONTROL_MODE_PID_B;
    }
}

void setGradientTarget(float grad)
{
    //change global variables
    gradient_setpoint = grad;
    control_mode_flags |= CONTROL_MODE_GRADIENT;
    control_mode_flags |= CONTROL_MODE_PID_A;
    control_mode_flags |= CONTROL_MODE_PID_B;
}

void setChanA_TemperatureTarget(float temp)
{
    //change global variables
    gradient_setpoint = 0.0;
    chanA_PID_setpoint    = temp;
    control_mode_flags &= ~CONTROL_MODE_GRADIENT;
    //control_mode_flags &= ~CONTROL_MODE_FUNC_A;
    control_mode_flags |=  CONTROL_MODE_PID_A;
}

void setChanB_TemperatureTarget(float temp)
{
    //change global variables
    gradient_setpoint = 0.0;
    chanB_PID_setpoint    = temp;
    control_mode_flags &= ~CONTROL_MODE_GRADIENT;
    //control_mode_flags &= ~CONTROL_MODE_FUNC_B;
    control_mode_flags |=  CONTROL_MODE_PID_B;
}

void setChanA_FuncOff()
{
    //change global variables
    chanA_FGen.setFuncOff();
    control_mode_flags &=  ~CONTROL_MODE_FUNC_A; 
}

void setChanB_FuncOff()
{
    //change global variables
    chanB_FGen.setFuncOff();
    control_mode_flags &=  ~CONTROL_MODE_FUNC_B; 
}

void setChanA_FuncSin(double freq, double amp, double phase)
{
    //change global variables
    chanA_FGen.setFuncSin(freq,amp,phase);
    control_mode_flags &= ~CONTROL_MODE_GRADIENT;
    control_mode_flags |=  CONTROL_MODE_FUNC_A; 
}

void setChanB_FuncSin(double freq, double amp, double phase)
{
    //change global variables
    chanB_FGen.setFuncSin(freq,amp,phase);
    control_mode_flags &= ~CONTROL_MODE_GRADIENT;
    control_mode_flags |=  CONTROL_MODE_FUNC_B; 
}

void funcSync()
{
    //change global variables
    chanA_FGen.resetTime();
    chanB_FGen.resetTime();
}

void printStatusYAML()
{
    // report all state variables in YAML format
    Serial.println("---");
    Serial.print("control_mode: ");
    Serial.println(control_mode_flags);
    Serial.print("gradient_setpoint: ");
    Serial.println(gradient_setpoint);
    Serial.print("temperatureA_measured: ");
    Serial.println(T_A);
    Serial.print("temperatureA_target: ");
    Serial.println(chanA_PID_setpoint);
    Serial.print("chanA_PID_output: ");
    Serial.println(chanA_PID_output);
    Serial.print("chanA_func_output: ");
    Serial.println(chanA_func_output);
    Serial.print("chanA_output: ");
    Serial.println(chanA_output);
    Serial.print("temperatureB_measured: ");
    Serial.println(T_B);
    Serial.print("temperatureB_target: ");
    Serial.println(chanB_PID_setpoint);
    Serial.print("chanB_PID_output: ");
    Serial.println(chanB_PID_output);
    Serial.print("chanB_func_output: ");
    Serial.println(chanB_func_output);
    Serial.print("chanB_output: ");
    Serial.println(chanB_output);
    Serial.print("temperatureC_measured: ");
    Serial.println(T_C);
    Serial.println("...");
}

//------------------------------------------------------------------------------
//COMMAND HANDLER FUNCTIONS - called by the SCmd dispatcher

void setGradientTargetCommand()
{
    float grad;
    char *arg;
    arg = SCmd.next();
    if (arg != NULL)
    {
        grad = atof(arg);
        setGradientTarget(grad);
    }
    else
    {
        Serial.println("### Error: GRAD requires 1 argument (float grad) ###"); 
    }
}

void setChanA_TemperatureTargetCommand()
{
    float temp;
    char *arg;
    arg = SCmd.next();
    if (arg != NULL)
    {
        temp = atof(arg);
        setChanA_TemperatureTarget(temp);
    }
    else
    {
        Serial.println("### Error: TEMP_A requires 1 argument (float temp) ###");
    }
}

void setChanB_TemperatureTargetCommand(){
    float temp;
    char *arg;
    arg = SCmd.next();
    if (arg != NULL)
    {
        temp = atof(arg);
        setChanB_TemperatureTarget(temp);
    }
    else
    {
        Serial.println("### Error: TEMP_B requires 1 argument (float temp) ###");
    }
}

void getStatusCommand(){
    char *arg;
    arg = SCmd.next();
    if (arg != NULL)
    {
        Serial.println("### Error: STATUS requires 0 arguments ###");
    }
    else
    {
       printStatusYAML();
    }
}

void setChanA_PIDModeCommand(){
    char *arg;    
    int cmp;
    
    arg = SCmd.next();
    if (arg != NULL)
    {
        cmp = strcmp(arg,"on");
        if (cmp == 0)
        {
            //Serial.println("### setting 'on' mode ###");            
            setChanA_PIDMode(1);
            return;
        }
        cmp = strcmp(arg,"off");
        if (cmp == 0)
        {
            //Serial.println("### setting 'off' mode ###");             
            setChanA_PIDMode(0);
            return;
        }
        //default case
        Serial.println("### Error: PID_A (char *mode) must be in {'on','off'} ###");
    }
    else
    {
        Serial.println("### Error: PID_A requires 1 argument (char *mode) {'on','off'} ###");
    }
}

void setChanB_PIDModeCommand(){
    char *arg;    
    int cmp;
    
    arg = SCmd.next();
    if (arg != NULL)
    {
        cmp = strcmp(arg,"on");
        if (cmp == 0)
        {
            //Serial.println("### setting 'on' mode ###");            
            setChanB_PIDMode(1);
            return;
        }
        cmp = strcmp(arg,"off");
        if (cmp == 0)
        {
            //Serial.println("### setting 'off' mode ###");             
            setChanB_PIDMode(0);
            return;
        }
        //default case
        Serial.println("### Error: PID_B (char *mode) must be in {'on','off'} ###");
    }
    else
    {
        Serial.println("### Error: PID_B requires 1 argument (char *mode) {'on','off'} ###");
    }
}

void setChanA_FuncCommand(){
    char *arg;    
    int cmp;
    float freq=1.0, amp=1.0, phase=0.0;

    arg = SCmd.next(); //get first argument
    if (arg != NULL)
    {
        //turn function off ----------------------------------       
        cmp = strcmp(arg,"off");
        if (cmp == 0)
        {
            setChanA_FuncOff();
            return;
        }          
        //sin function ----------------------------------       
        cmp = strcmp(arg,"sin");
        if (cmp == 0)
        {
            arg = SCmd.next(); //get second argument
            if (arg != NULL)
            {
                freq = atof(arg);
                arg = SCmd.next(); //get third argument
                if (arg != NULL)
                {
                    amp = atof(arg);
                    arg = SCmd.next(); //get fourth argument
                    if (arg != NULL)
                    {
                        phase = atof(arg);
                    }    
                }    
            } 
            setChanA_FuncSin(freq, amp, phase);
            return;
        }
        //default case -----------------------------------
        Serial.println("### Error: FUNC_A (char *func) must be in {'sin'} ###");            
    }
    else
    {
        Serial.println("### Error: FUNC_A requires at least 1 argument (char *func) ###");
    }
}

void setChanB_FuncCommand(){
    char *arg;    
    int cmp;
    float freq=1.0, amp=1.0, phase=0.0;

    arg = SCmd.next(); //get first argument
    if (arg != NULL)
    {
        //turn function off ----------------------------------       
        cmp = strcmp(arg,"off");
        if (cmp == 0)
        {
            setChanB_FuncOff();
            return;
        }        
        //sin function --------------------------------------       
        cmp = strcmp(arg,"sin");
        if (cmp == 0)
        {
            arg = SCmd.next(); //get second argument
            if (arg != NULL)
            {
                freq = atof(arg);
                arg = SCmd.next(); //get third argument
                if (arg != NULL)
                {
                    amp = atof(arg);
                    arg = SCmd.next(); //get fourth argument
                    if (arg != NULL)
                    {
                        phase = atof(arg);
                    }    
                }    
            } 
            setChanB_FuncSin(freq, amp, phase);
            return;
        }
        //default case -----------------------------------
        Serial.println("### Error: FUNC_B (char *func) must be in {'sin'} ###");        
    }
    else
    {
        Serial.println("### Error: FUNC_B requires at least 1 argument (char *func) ###");
    }
}

void funcSyncCommand(){
    char *arg;
    arg = SCmd.next();
    if (arg != NULL)
    {
        Serial.println("### Error: FUNC_SYNC requires 0 arguments ###");
    }
    else
    {
       funcSync();
    }
}

void unrecognizedCommand()
{
    Serial.println("### Error: command not recognized ###");
}
