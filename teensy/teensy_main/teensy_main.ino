#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_BMP280.h>
#include <utility/imumaths.h>
#include <Adafruit_GPS.h>

#define GPSSerial Serial1

Adafruit_GPS GPS(&GPSSerial);

Adafruit_BMP280 bmp;
double base_altitude = 0;
double* alti_offset = &base_altitude;

Adafruit_BNO055 bno = Adafruit_BNO055(55);

int packetNo = 0;
// Flags to tell if the BMP and BNO sensors are connected
bool BNO_CONNECTED;
bool BMP_CONNECTED;

uint32_t timer = millis();

void setup(void) 
{
  Serial.begin(115200);

  if(!bno.begin()){
    Serial.print("No BNO055 Detected!");
    while(1);
    }
  else
    BNO_CONNECTED = true;

   if (!bmp.begin()) {
    Serial.println("No BMP280 Detected!");
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

  // 9600 NMEA is the default baud rate for Adafruit MTK GPS's- some use 4800
  GPS.begin(9600);
  // uncomment this line to turn on RMC (recommended minimum) and GGA (fix data) including altitude
  // GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // uncomment this line to turn on only the "minimum recommended" data
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  // For parsing data, we don't suggest using anything but either RMC only or RMC+GGA since
  // the parser doesn't care about other sentences at this time
  // Set the update rate
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_10HZ); // 1 Hz update rate
  // For the parsing code to work nicely and have time to sort thru the data, and
  // print it out we don't suggest using anything higher than 1 Hz

  // Request updates on antenna status, comment out to keep quiet
  // GPS.sendCommand(PGCMD_ANTENNA);
  
  delay(1000);
}

void loop(void) 
{
//  BNO_CONNECTED = bno.isFullyCalibrated();
//  BMP_CONNECTED = bmp.isConnected();

//  Serial.println(BNO_CONNECTED);
//  Serial.println(BMP_CONNECTED);

  char c = GPS.read();

  if (GPS.newNMEAreceived()) {
    // a tricky thing here is if we print the NMEA sentence, or data
    // we end up not listening and catching other sentences!
    // so be very wary if using OUTPUT_ALLDATA and trying to print out data
    //Serial.println(GPS.lastNMEA()); // this also sets the newNMEAreceived() flag to false
    if (!GPS.parse(GPS.lastNMEA())) // this also sets the newNMEAreceived() flag to false
      return; // we can fail to parse a sentence in which case we should just wait for another
  }
  // if millis() or timer wraps around, we'll just reset it
  if (timer > millis()) timer = millis();

  // approximately every 2 seconds or so, print out the current stats
  if (millis() - timer > 100) {
    timer = millis(); // reset the timer

    imu::Quaternion quat = bno.getQuat();           // Request quaternion data from BNO055
    imu::Vector<3> vaccel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
    imu::Vector<3> laccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    imu::Vector<3> gvector = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
    imu::Vector<3> angular_vel = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
    imu::Vector<3> magneto = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);
  
  
    StaticJsonDocument<550> doc;                      //PACKET SIZE = 414
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
    imu.add(gvector.x());
    imu.add(gvector.y());
    imu.add(gvector.z());
    imu.add(angular_vel.x());
    imu.add(angular_vel.y());
    imu.add(angular_vel.z());
    imu.add(magneto.x());
    imu.add(magneto.y());
    imu.add(magneto.z());

    // Serial.print(GPS.latitudeDegrees);
    // Serial.print(GPS.longitudeDegrees);
    gps.add(GPS.latitudeDegrees);
    gps.add(GPS.longitudeDegrees);

    serializeJson(doc, Serial);
    Serial.println("");
  
    packetNo++;
  }
}
