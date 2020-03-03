//////////////////////////////////ISP_Avionics//////////////////////////////////
/*  Created: 3.2.20
 *     Name: BNO055
 * Function: Gets orientation and acceleration data from the BNO055 sensor and 
 *           dispays it on the serial monitor.
 *    Notes: Default I2C addr = 0x28, if ADR pin set high, addr = 0x29.  
 *           Connect SCL to SCL pin (analog 5) pin 19
             Connect SDA to SDA pin (analog 4) pin 18
             Connect VDD to 3-5V DC
             Connect GROUND to common ground
             Originally created by Blake Shaffer, contact for questions.
 *  Updates: 
 */
///////////////////////////////////Libraries!///////////////////////////////////
#include <Wire.h>             //library for I2C communication
#include <Adafruit_BNO055.h>  //predefined funcs for BNO055 sensor
#include <Adafruit_Sensor.h>  //standard adafruit sensor library for easy use
#include <utility/imumaths.h> //specific math library for BNO055 IMU sensor

/////////////////////////////Variables and #Defines/////////////////////////////
#define BNO055_DELAY_MS 100  //delay time (ms) between new samples

//BNO055 9-axis Abs. Orientation Sensor
volatile bool BNO_CONNECTED;  //tells if BNO055 is connected or not
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);  //55=device id, 0x28=I2C addr

//////////////////////////////////////MAIN//////////////////////////////////////
void setup(){
  Serial.begin(115200); //begin communication with serial monitor
  Serial.println("Orientation Sensor Test");  //print welcome message
  Serial.println();                           //print newline

  BNO_setup();  //setup the BNO055 sensor 
}

void loop(){
  sensors_event_t event;  //declare event var
  bno.getEvent(&event);   //grab new event

  printData(event);       //print data to serial monitor
  delay(BNO055_DELAY_MS); //delay to wait for new data
}

///////////////////////////////////Functions!///////////////////////////////////
/*******************************************************************************
*        Name: BNO_setup
* Description: Sets up the BNO055 sensor. Checks it's status to see if it is 
*              connected, then prints its basic information.
*       Input: VOID
*  Out/Modify: VOID, modifies "BNO_CONNECTED", =TRUE if connected, FALSE if not
*******************************************************************************/
void
BNO_setup(){
  BNO_status(); //check connection of BNO055

  if(BNO_CONNECTED){
    displayBNOdetails();     //display basic sensor info
    displayBNOstatus();      //display current sensor status
    bno.setExtCrystalUse(true); //set crystal oscillator for measurements
  }
  else{
    Serial.println("BNO055: Something went wrong, check connections.");
    while(1);   //infinite loop
  }
}

/*******************************************************************************
*        Name: printData
* Description: Prints data from BNO055 sensor to the serial monitor.
*       Input: sensors_event_t event = struct to hold event data
*  Out/Modify: VOID
*******************************************************************************/
void
printData(sensors_event_t event){
  //reported in degrees
  Serial.print("X: ");   Serial.print(event.orientation.x, 4);
  Serial.print("\tY: "); Serial.print(event.orientation.y, 4);
  Serial.print("\tZ: "); Serial.println(event.orientation.z, 4);

  //reported in degrees
  Serial.print("Roll ");      Serial.print(event.orientation.roll, 4);
  Serial.print("\tPitch ");   Serial.print(event.orientation.pitch, 4);
  Serial.print("\tHeading "); Serial.println(event.orientation.heading, 4);

  //reported in m/s^2
  Serial.print("Xaccel: ");   Serial.print(event.acceleration.x, 4);
  Serial.print("\tYaccel: "); Serial.print(event.acceleration.y, 4);
  Serial.print("\tZaccel: "); Serial.println(event.acceleration.z, 4);

  //reported in *C
  Serial.print("Temperature: ");
  Serial.print(event.temperature);
  Serial.println(" *C");
}

/*******************************************************************************
*        Name: BNO_status
* Description: Ensures BNO055 is connected. Attempts to connect 3 times before
*              calling it quits. Prints messages updating the status of test.
*       Input: VOID
*  Out/Modify: VOID, modifies BNO_CONNECTED
*******************************************************************************/
void
BNO_status(void){
  Serial.println("Checking status of BN0055.");
  for(int i=0; i<3; i++){     //loop 3 times to check connection
    Serial.print("On try ");  //print try message
    Serial.print(i);          //print try number
    Serial.print(": ");       //print formatting
    
    if (bno.begin()){                         //begin() = TRUE if sensor found
      Serial.println("BNO055 Detected!");     //print success message
      BNO_CONNECTED = true;                   //signal connection is made
      break;                                  //exit loop
    }
    else{
      Serial.println("No BNO055 Detected!");  //print error message
      BNO_CONNECTED = false;                  //signal no connection
    }
  }
  Serial.println(); //print newline
}

/*******************************************************************************
*        Name: displayBNOdetails
* Description: Displays some basic information on this sensor from the unified
*              sensor API sensor_t type (see Adafruit_Sensor for more info).
*       Input: VOID
*  Out/Modify: VOID
*******************************************************************************/
void 
displayBNOdetails(void){
  sensor_t sensor;        //declare sensor var
  bno.getSensor(&sensor); //grab sensor details

  //Print sensor details to serial monitor
  Serial.println("------------------------------------");
  Serial.print  ("Sensor:     "); Serial.println(sensor.name);
  Serial.print  ("Driver Ver: "); Serial.println(sensor.version);
  Serial.print  ("Type: ");       Serial.println(sensor.type);
  Serial.print  ("Unique ID:  "); Serial.println(sensor.sensor_id);
  Serial.print  ("Max Value:  "); Serial.println(sensor.max_value);
  Serial.print  ("Min Value:  "); Serial.println(sensor.min_value);
  Serial.print  ("Resolution: "); Serial.println(sensor.resolution);
  Serial.println("------------------------------------");
  Serial.println();
}

/*******************************************************************************
*        Name: displayBNOstatus
* Description: Display some basic info about the sensor status. Mostly used for
*              debugging purposes.
*       Input: VOID
*  Out/Modify: VOID
*******************************************************************************/
void
displayBNOstatus(void){
  uint8_t system_status, self_test_results, system_error; //declare 8-bit vars
  system_status = self_test_results = system_error = 0;   //assign init vals
  
  bno.getSystemStatus(&system_status, &self_test_results, &system_error);

  //Print status data to serial monitor
  Serial.println();
  Serial.print("System Status: 0x"); Serial.println(system_status, HEX);
  Serial.print("Self Test:     0x"); Serial.println(self_test_results, HEX);
  Serial.print("System Error:  0x"); Serial.println(system_error, HEX);
  Serial.println();
}

/*******************************************************************************
*        Name: 
* Description: 
*       Input: 
*  Out/Modify: 
*******************************************************************************/

//////////////////////////////////ISP_Avionics//////////////////////////////////
