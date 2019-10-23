#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <Adafruit_BMP280.h>
#include <utility/imumaths.h>

Adafruit_BMP280 bmp;
double base_altitude = 0;
double* alti_offset = &base_altitude;
  
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

float bno_data[22] = {(bmp.readTemperature()),(bmp.readPressure()),((bmp.readAltitude(1013.25))-(*alti_offset+.1)),
                       ((quat.w())),((quat.x())),((quat.y())),((quat.z())),
                       (vaccel.x()),(vaccel.y()),(vaccel.z()),
                       (laccel.x()),(laccel.y()),(laccel.z()),
                       (gvector.x()),(gvector.y()),(gvector.z()),
                       (angular_vel.x()),angular_vel.y(),angular_vel.z(),
                       (magneto.x()),(magneto.y()),(magneto.z()),
                       };

for(int i=0;i<22;i++){
  Serial.print(bno_data[i]);
  Serial.print(",\t");
  }
Serial.println("");

  delay(100);
}
