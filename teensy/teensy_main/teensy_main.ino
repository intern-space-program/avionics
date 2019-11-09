/*  .................Intern Space Program Avionics Division Teensy Branch...........
 * 
 * This code is designed to read data from a Pressure Sensor, an IMU, and a GPS,
 * then output the format into a Json Object.
 * 
 * It includes a startup sequence that completes a handshake with a 
 * Raspberry Pi and checks for the sensors to be connected
 * 
 */


//______________________________Libraries______________________________________//


#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_BMP280.h>
#include <utility/imumaths.h>
#include <Adafruit_GPS.h>




//___________________________Global Assignments_________________________________//


//General Assignments ....................
int packetNo = 0;
bool BNO_CONNECTED;   // Flags to tell if the BMP and BNO sensors are connected
bool BMP_CONNECTED;   // Flags to tell if the BMP and BNO sensors are connected
bool GPS_CONNECTED;   // Flags to tell if the GPS is connected.

uint32_t timer = millis();
#define piSerial Serial  

//GPS Assignments..........................
#define GPSSerial Serial1
Adafruit_GPS GPS(&GPSSerial);


//BMP 280 Related Assignments ...............
Adafruit_BMP280 bmp;
double base_altitude = 0;
double* alti_offset = &base_altitude;


//BNO 055 Related Assignments................
Adafruit_BNO055 bno = Adafruit_BNO055(55);

//________________________________________________________________________________//




////////////////////////////////////////////////////////////////////////////////////
//.................................Void Setup.....................................//
////////////////////////////////////////////////////////////////////////////////////

void setup(void) 
{
  piSerial.begin(115200);
  piSerial.print("dump_init");
  

/*
  //__________________________________Initial Handshake Sequence____________________________//
  while (1){
    while(!piSerial.available());
    if (piSerial.find("startup")){
        Serial.println("starting");
        break;
    }
  }
*/

//____________________________________Startup Sequence_____________________________________// 

//Start the BNO 055..................................................
  if(!bno.begin()){
    piSerial.print("No BNO055 Detected!");
    while(1);
    }
  else
    BNO_CONNECTED = true;

//Start the BNO 055..................................................
   if (!bmp.begin()) {
    piSerial.println("No BMP280 Detected!");
    while (1);
    }
  else
    BMP_CONNECTED = true;
  
   bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     /* Operating Mode. */
                Adafruit_BMP280::SAMPLING_X2,     /* Temp. oversampling */
                Adafruit_BMP280::SAMPLING_X16,    /* Pressure oversampling */
                Adafruit_BMP280::FILTER_X16,      /* Filtering. */
                Adafruit_BMP280::STANDBY_MS_500); /* Standby time. */

   *alti_offset = bmp.readAltitude(1013.25);
   bno.setExtCrystalUse(true);


//Start the Adafruit GPS.........................................................
  // 9600 NMEA is the default baud rate for Adafruit MTK GPS's- some use 4800
  GPS.begin(9600);
  // uncomment this line to turn on RMC (recommended minimum) and GGA (fix data) including altitude
  // GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // uncomment this line to turn on only the "minimum recommended" data
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // For parsing data, we don't suggest using anything but either RMC only or RMC+GGA since
  // the parser doesn't care about other sentences at this time
  // Set the update rate
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_10HZ); // 1 Hz update rate
  // For the parsing code to work nicely and have time to sort thru the data, and
  // print it out we don't suggest using anything higher than 1 Hz

  // Request updates on antenna status, comment out to keep quiet
  // GPS.sendCommand(PGCMD_ANTENNA);
  
  delay(1000);
//__________________________________Final Handshake Sequence______________________________// 
/*
  for(int i = 0; i < 3; i++){
     piSerial.println("initialized");
  }


  while (1){
    while(!piSerial.available());
    if (piSerial.find("dump")){
        break;
    }
  }
 */
} 


////////////////////////////////////////////////////////////////////////////////////
//.................................Void Setup.....................................//
////////////////////////////////////////////////////////////////////////////////////

void loop(void) {

//_______________________________Check for Sensor Connection______________//
//  BNO_CONNECTED = bno.isFullyCalibrated();
//  BMP_CONNECTED = bmp.isConnected();

//  Serial.println(BNO_CONNECTED);
//  Serial.println(BMP_CONNECTED);


//_______________________________________Sample GPS________________________//

  GPS.read();

  if (GPS.newNMEAreceived()) {
    // a tricky thing here is if we print the NMEA sentence, or data
    // we end up not listening and catching other sentences!
    // so be very wary if using OUTPUT_ALLDATA and trying to print out data
    //Serial.println(GPS.lastNMEA()); // this also sets the newNMEAreceived() flag to false
    if (!GPS.parse(GPS.lastNMEA())) // this also sets the newNMEAreceived() flag to false
      return; // we can fail to parse a sentence in which case we should just wait for another
  }
  //if millis() or timer wraps around, we'll just reset it
  if (timer > millis()) timer = millis();
  if (millis() - timer > 100) {
    timer = millis(); // reset the timer


 //

    imu::Quaternion quat = bno.getQuat();           
    imu::Vector<3> vaccel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
    imu::Vector<3> laccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    imu::Vector<3> gvector = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
    imu::Vector<3> angular_vel = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
    imu::Vector<3> magneto = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);
  
 //_________________________________Create JSON Array_________________________________________// 
    StaticJsonDocument<550> doc;                      //PACKET SIZE = 550

    JsonArray hdr = doc.createNestedArray("hdr");           //create the Json Object
    JsonArray tpa = doc.createNestedArray("tpa");
    JsonArray imu = doc.createNestedArray("imu");
    JsonArray gps = doc.createNestedArray("gps");
    hdr.add(packetNo);                      //each packet is assigned a sequential number
    hdr.add(millis());                          //creates a millisecond readout based on the Arduino's internal clock    
    //creates a json nested object for temp, press, alti
  
    tpa.add(bmp.readTemperature());       
    tpa.add(bmp.readPressure());
    tpa.add((bmp.readAltitude(1013.25))-(*alti_offset+.1));
    
    imu.add(vaccel.x());
    imu.add(vaccel.y());
    imu.add(vaccel.z());
    imu.add(quat.w());
    imu.add(quat.x());
    imu.add(quat.y());
    imu.add(quat.z());
    imu.add(laccel.x());
    imu.add(laccel.y());
    imu.add(laccel.z());
    imu.add(angular_vel.x());
    imu.add(angular_vel.y());
    imu.add(angular_vel.z());
    

    // Serial.print(GPS.latitudeDegrees);
    // Serial.print(GPS.longitudeDegrees);
    gps.add(GPS.latitudeDegrees);
    gps.add(GPS.longitudeDegrees);
    gps.add(GPS.altitude);

    
    //_________________________________Connection Checking_________________________________________// 
    if ((gps[1] == 0) || (gps[0] ==0)) {
      GPS_CONNECTED = 1;
    }
    

    if ((tpa[2] < 0) || (tpa[2] > 3300)) {
      BMP_CONNECTED = 0;
    }
    serializeJson(doc, piSerial);
    piSerial.println("");
    
    packetNo++;
  }
}
