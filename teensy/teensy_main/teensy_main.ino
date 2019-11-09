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
//_____________________________________________________________________________//

//_______________________________Macros________________________________________//
#define piSerial Serial
#define GPSSerial Serial1
//_____________________________________________________________________________//

//___________________________Global Assignments_________________________________//
// IMU variables
imu::Quaternion quat;
imu::Vector<3> vaccel;
imu::Vector<3> laccel;
imu::Vector<3> gvector;
imu::Vector<3> angular_vel;
imu::Vector<3> magneto;

//General Assignments ....................
int packetNo = 0;

// Flags to tell if the BNO, BMP, and GPS sensors are connected
bool BNO_CONNECTED;
bool BMP_CONNECTED;
bool GPS_CONNECTED;

uint32_t timer = millis();


//GPS Assignments..........................

Adafruit_GPS GPS(&GPSSerial);


//BMP 280 Related Assignments ...............
Adafruit_BMP280 bmp;
double base_altitude = 0;
double gps_base_altitude =0;
double* alti_offset_address = &base_altitude;
double* gps_alti_offset_address = &gps_base_altitude;
bool altitude_valid = false;

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

//Start and set the BNO 055..................................................
  uint8_t i;
  for(i = 0; i < 3; i++) {
    piSerial.print("On try ");
    piSerial.print(i);
    piSerial.print(": ");
    if(!bno.begin()) {
      piSerial.print("No BNO055 Detected!");
      BNO_CONNECTED = false;
    }
    else {
      piSerial.print("BNO055 Detected!");
      BNO_CONNECTED = true;
      break;
    }
  }
  


//Start and set the BMP 055..................................................
  for(i = 0; i < 3; i++){
    piSerial.print("On try ");
    piSerial.print(i);
    piSerial.print(": ");
    if (!bmp.begin()) {
      piSerial.println("No BMP280 Detected!");
      BMP_CONNECTED = false;
    }
    else {
      piSerial.println("BMP280 Detected!");
      BMP_CONNECTED = true;
      break;
    }
  }


    if(BMP_CONNECTED){
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     /* Operating Mode. */
                    Adafruit_BMP280::SAMPLING_X2,     /* Temp. oversampling */
                    Adafruit_BMP280::SAMPLING_X16,    /* Pressure oversampling */
                    Adafruit_BMP280::FILTER_X16,      /* Filtering. */
                    Adafruit_BMP280::STANDBY_MS_500); /* Standby time. */

    *alti_offset_address = bmp.readAltitude(1013.25);
  }
  
  if(BNO_CONNECTED){
    bno.setExtCrystalUse(true);
  }
//.........................................................................//

//Start and set the Adafruit GPS.............................................
  GPS.begin(9600);
  GPS_CONNECTED = true;
  if(GPS_CONNECTED){
    piSerial.println("GPS Detected!");
    /*  Uncomment this line to turn on RMC (recommended minimum)
        and GGA (fix data) including altitude */
    GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);

    /*  Uncomment this line to turn on only the 
        "minimum recommended" data */
    //GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);

    /*  For parsing data, we don't suggest using anything but 
        either RMC only or RMC+GGA since the parser doesn't care 
        about other sentences at this time*/

    /*  SET UPDATE RATE: 
        For the parsing code to work nicely and have time to sort 
        thru the data, and print it out we don't suggest using 
        anything higher than 1 Hz */
    GPS.sendCommand(PMTK_SET_NMEA_UPDATE_10HZ); // 1 Hz update rate

    /* Request updates on antenna status, comment out to keep quiet*/
    // GPS.sendCommand(PGCMD_ANTENNA);
    
    delay(1000);
  }
//__________________________________Final Handshake Sequence______________________________// 


  for(int i = 0; i < 3; i++){
     piSerial.println("initialized");
  }






  while (1){
    while(!piSerial.available());
    if (piSerial.find("dump")){
        break;
    }
  }

//__________________________________Final Handshake Sequence______________________________//
  *gps_alti_offset_address = 0.0;
} 


////////////////////////////////////////////////////////////////////////////////////
//.................................Void Loop......................................//
////////////////////////////////////////////////////////////////////////////////////
void loop(void) {
//_________________________________________________________________________//
//_______________________________Sample GPS________________________________//
//_________________________________________________________________________//
  GPS.read();
  if (GPS.newNMEAreceived()) {
    /*  A tricky thing here is if we print the NMEA sentence, 
        or data we end up not listening and catching other 
        sentences! So be very wary if using OUTPUT_ALLDATA and
        trying to print out data. this also sets the newNMEAreceived() 
        flag to false */

    //Serial.println(GPS.lastNMEA()); // 
    
    /* This also sets the newNMEAreceived() flag to false */
    if (!GPS.parse(GPS.lastNMEA())) 
      /* we can fail to parse a sentence in which case we should 
         just wait for another */
      return; 
  }

  /* if millis() or timer wraps around, we'll just reset it */
  if (timer > millis()) 
    timer = millis();

  /////////////////////////////////////////////////////////////////////////////////// 
  //  READ SENSORS AND SEND DATA AT 10Hz
  ///////////////////////////////////////////////////////////////////////////////////
  if (millis() - timer > 100) 
  {
    GPS_CONNECTED = false;
    //_____________Reset Timer______________//
      timer = millis(); // reset the timer
      
    //_______________Read BNO_______________//
      quat = bno.getQuat();           
      vaccel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
      laccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
      gvector = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
      angular_vel = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
      magneto = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);
    
    //___________Create JSON Array__________// 
      StaticJsonDocument<550> doc; //PACKET SIZE = 550

      JsonArray hdr = doc.createNestedArray("hdr"); //create the Json Object
      JsonArray tpa = doc.createNestedArray("tpa");
      JsonArray imu = doc.createNestedArray("imu");
      JsonArray gps = doc.createNestedArray("gps");
      hdr.add(packetNo); //each packet is assigned a sequential number
      hdr.add(millis()); //creates a millisecond readout based on the Arduino's internal clock    
      
      /*creates a json nested object for temp, press, alti*/

    //_____________Read TPA Data_____________//
      tpa.add(bmp.readTemperature());       
      tpa.add(bmp.readPressure());
      tpa.add((bmp.readAltitude(1013.25))-(*alti_offset_address+.1));
      
    //________________Read IMU_______________//
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
      imu.add(gvector.x());
      imu.add(gvector.y());
      imu.add(gvector.z());
      imu.add(angular_vel.x());
      imu.add(angular_vel.y());
      imu.add(angular_vel.z());
      imu.add(magneto.x());
      imu.add(magneto.y());
      imu.add(magneto.z());

    //_______________Read GPS______________//
      if (GPS.altitude != 0 && altitude_valid == false)
      {
        *gps_alti_offset_address = GPS.altitude;
        altitude_valid = true;
      }
      gps.add(GPS.latitudeDegrees);
      gps.add(GPS.longitudeDegrees);
      gps.add(GPS.altitude - *gps_alti_offset_address);

    //__________Check Connections__________//

      if ((gps[1] != 0) || (gps[0]!= 0)) {GPS_CONNECTED = true;}
  
      if ((tpa[2] < -50) || (tpa[2] > 3300)) {BMP_CONNECTED = false, BNO_CONNECTED = false;}
  
      if (imu[3] == 0 && imu[4] == 0 && imu[5] == 0 && imu[6] == 0)
      {
        BNO_CONNECTED = false;
      }

      hdr.add(GPS_CONNECTED);
      hdr.add(BMP_CONNECTED);
      hdr.add(BNO_CONNECTED);


    //______________Send Data______________//
      serializeJson(doc, piSerial);
      piSerial.println("");
      
      packetNo++;
  }
  ///////////////////////////////////////////////////////////////////////////////////
}
