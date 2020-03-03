//////////////////////////////////ISP_Avionics//////////////////////////////////
/*  Created: 2.28.20
 *     Name: BMP280
 * Function: Communicates w/ BMP280 module from a Teensy 3.2 to display
 *           pressure, temp, and altitude data on the serial monitor. Must be
 *           modified to send data to the Raspi 0 via UART (serial).
 *           Originally created by Blake Shaffer, contact for questions.
 *  Updates:
 *
 */
///////////////////////////////////Libraries!///////////////////////////////////
#include <Adafruit_BMP280.h>  //predefined funcs for BMP280 sensor

/////////////////////////////Variables and #Defines/////////////////////////////
#define BMP_CS  10            //assign chip select to pin10
#define sealevel_hPa  1008.7  //pressure at sea level in hectopascals (hPa)

//BMP280 Pressure & Temp Sensor
Adafruit_BMP280 bmp(BMP_CS);  //object define for hardware SPI
double base_altitude;         //var to hold starting altitude of sensor
double current_altitude;      //var to hold the current altitude of sensor
volatile bool BMP_CONNECTED;  //tells if BMP280 is connected or not

//////////////////////////////////////MAIN//////////////////////////////////////
void setup(){ 
  Serial.begin(9600);                 //begin communication w/ serial monitor
  Serial.println(F("BMP280 test"));   //print welcome message

  BMP_setup();    //setup BMP280 to capture data
}

void loop(){
  Serial.print(F("Temperature = "));                      //print message
  Serial.print(( (9.0/5.0)*bmp.readTemperature() )+32.0); //print temp in F
  Serial.println(" *F");                                  //print unit
  
  Serial.print(F("Pressure = "));   //print message
  Serial.print(bmp.readPressure()); //print pressure in Pa
  Serial.println(" Pa");            //print unit

  Serial.print(F("Approx altitude = "));                       //print message
  Serial.print(bmp.readAltitude(sealevel_hPa)-base_altitude);  //print alt
  Serial.println(" m");                                        //print unit
  
  Serial.println(); //print newline
  delay(500);       //wait to retreive new data
}

///////////////////////////////////functions!///////////////////////////////////
/*******************************************************************************
*        Name: BMP_setup
* Description: Sets up necessary parameters for BMP280.
*       Input: VOID
*  Out/Modify: VOID, modifies base_altitude, gives it a value
*******************************************************************************/
void
BMP_setup(){
  BMP_status(); //check connection of BMP280

  if(BMP_CONNECTED){
    //Default settings from datasheet.
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     //Operating Mode
                    Adafruit_BMP280::SAMPLING_X2,     //Temp. oversampling
                    Adafruit_BMP280::SAMPLING_X16,    //Pressure oversampling
                    Adafruit_BMP280::FILTER_X16,      //Filtering
                    Adafruit_BMP280::STANDBY_MS_500); //Standby time  
    base_altitude = bmp.readAltitude(sealevel_hPa);   //read current altitude
  }
  else{
    Serial.println("BMP280: Something went wrong, check connections.");
    while(1);   //infinite loop
  }
}

/*******************************************************************************
*        Name: BMP_status
* Description: Ensures BMP280 is connected. Attempts to connect 3 times before
*              calling it quits. Prints messages updating the status of test.
*       Input: VOID
*  Out/Modify: VOID, modifies "BMP_CONNECTED", =TRUE if connected, FALSE if not
*******************************************************************************/
void
BMP_status(void){
  Serial.println("Checking status of BMP280.");
  for(int i=0; i<3; i++){     //loop 3 times to check connection
    Serial.print("On try ");  //print try message
    Serial.print(i);          //print try number
    Serial.print(": ");       //print formatting
    
    if (bmp.begin()){                         //begin() = TRUE if sensor found
      Serial.println("BMP280 Detected!");     //print success message
      BMP_CONNECTED = true;                   //signal connection is made
      break;                                  //exit loop
    }
    else{
      Serial.println("No BMP280 Detected!");  //print error message
      BMP_CONNECTED = false;                  //signal no connection
    }
  }
  Serial.println(); //print newline
}

/*******************************************************************************
*        Name: 
* Description: 
*       Input: 
*  Out/Modify: 
*******************************************************************************/
//////////////////////////////////ISP_Avionics//////////////////////////////////
