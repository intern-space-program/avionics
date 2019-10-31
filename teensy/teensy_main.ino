#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_BMP280.h>
#include <utility/imumaths.h>
//#include <Adafruit_GPS.h>

Adafruit_BMP280 bmp;
double base_altitude = 0;
double* alti_offset = &base_altitude;
int packetNo = 0;
Adafruit_BNO055 bno = Adafruit_BNO055(55);


void setup(void) 
{
  Serial.begin(9600);
  
  if(!bno.begin()){
    Serial.print("No BNO055 Detected!");
    while(1);
    }

   if (!bmp.begin()) {
    Serial.println("No BMP280 Detected!");
    while (1);
    }

  StaticJsonDocument<200> doc;


     bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     /* Operating Mode. */
                  Adafruit_BMP280::SAMPLING_X2,     /* Temp. oversampling */
                  Adafruit_BMP280::SAMPLING_X16,    /* Pressure oversampling */
                  Adafruit_BMP280::FILTER_X16,      /* Filtering. */
                  Adafruit_BMP280::STANDBY_MS_500); /* Standby time. */

 *alti_offset = bmp.readAltitude(1013.25);
 bno.setExtCrystalUse(true);
  
  delay(1000);
    
  
}

void loop(void) 
{




imu::Quaternion quat = bno.getQuat();           // Request quaternion data from BNO055
imu::Vector<3> vaccel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
imu::Vector<3> laccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
imu::Vector<3> gvector = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
imu::Vector<3> angular_vel = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
imu::Vector<3> magneto = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);

  
  
  
  
/*// This block creates a float array from samples of both the BMP and the BNO 
float bno_data[22] = { 
                       (bmp.readTemperature()),(bmp.readPressure()),((bmp.readAltitude(1013.25))-(*alti_offset+.1)),
                       ((quat.w())),((quat.x())),((quat.y())),((quat.z())),
                       (vaccel.x()),(vaccel.y()),(vaccel.z()),
                       (laccel.x()),(laccel.y()),(laccel.z()),
                       (gvector.x()),(gvector.y()),(gvector.z()),
                       (angular_vel.x()),angular_vel.y(),angular_vel.z(),
                       (magneto.x()),(magneto.y()),(magneto.z()),
                       };
*/








StaticJsonDocument<414> doc;                      //PACKET SIZE = 414
JsonObject root = doc.to<JsonObject>();           //create the Json Object
root["packetNo"] = packetNo;                      //each packet is assigned a sequential number
root["time"] = millis();                          //creates a millisecond readout based on the Arduino's internal clock    
JsonObject tpa = root.createNestedObject("tpa");  //creates a json nested object for temp, press, alti
tpa["temp"] = (bmp.readTemperature());       
tpa["pres"] = (bmp.readPressure());
tpa["alti"] = ((bmp.readAltitude(1013.25))-(*alti_offset+.1));
JsonObject imu = root.createNestedObject("imu");
imu["vaccelx"]= (vaccel.x()),
imu["vaccely"]= (vaccel.y()),
imu["vaccelz"]= (vaccel.z()),
imu["quatw"]= (quat.w());
imu["quatx"]= (quat.x()),
imu["quaty"]= (quat.y()),
imu["quatz"]= (quat.z()),
imu["laccelx"]= (laccel.x()),
imu["laccely"]= (laccel.y()),
imu["laccelz"]= (laccel.z()),
imu["gvectorx"]= (gvector.x()),
imu["gvectory"]= (gvector.y()),
imu["gvectorz"]= (gvector.z()),
imu["angvelx"]= (angular_vel.x()),
imu["angvely"]= (angular_vel.y()),
imu["angvelz"]= (angular_vel.z()),
imu["magx"]= (magneto.x()),
imu["magy"]= (magneto.y()),
imu["magz"]= (magneto.z()),

serializeJsonPretty(root, Serial);


  packetNo ++;
  delay(90);
}
