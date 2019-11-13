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

#define piSerial Serial2 //#PI SERIAL IS CONNECTED TO TX2/RX2 PORTS!!!!! 
#define GPSSerial Serial1

//___________________________Global Assignments_________________________________//

//General Assignments ....................
int packetNo = 0;
int json_packet_size = 500;
int minimum_calibration_time = 30000;  //milliseconds
int maximum_calibration_time = 60000;  //milliseconds

// Flags to tell if the BNO, BMP, and GPS sensors are connected
volatile bool BNO_CONNECTED;
volatile bool BMP_CONNECTED;
volatile bool GPS_CONNECTED;

uint32_t timer = millis(); // A timer used to determine when to sample the sensors

//GPS Assignments..........................
bool altitude_valid = false;                          // A flag that determines when actual altitude is available
Adafruit_GPS GPS(&GPSSerial);                         // Sets and creates the GPS object.
double gps_base_altitude = 0;                         // Memory location for GPS base altitude
double* gps_alti_offset_address = &gps_base_altitude; // Offset for the GPS for launch reference frame

//BMP 280 Related Assignments ...............
Adafruit_BMP280 bmp;                          // BMP object to set and call data point
double base_altitude = 0;                     // Memory location for the offset for the BMP
double* alti_offset_address = &base_altitude; // Offset for the base altitude for the BMP
JsonArray tpa;

//BNO 055 Related Assignments................
Adafruit_BNO055 bno = Adafruit_BNO055(55);
imu::Quaternion quat;         // 4 dimensional quaternion vector
imu::Vector<3> vaccel;        // 3-dimensional Vector acceleration (non-conservative)
imu::Vector<3> laccel;        // 3-dimensional Vector acceleration (conservative)
imu::Vector<3> angular_vel;   // 3-dimensional angular velocity vector

// Function definitions
void sample_GPS();
JsonArray fill_in_bmp_array(JsonArray);
JsonArray fill_in_bno_array(JsonArray);
JsonArray fill_in_gps_array(JsonArray);
JsonArray fill_in_hdr_array(JsonArray);
void set_sensor_status_flags(JsonArray, JsonArray, JsonArray);
void set_up_gps();
void set_up_bmp();
void check_for_bmp_status();
void set_up_imu();
void initial_hand_shake_sequence();
void final_hand_shake_sequence();
void pull_data_and_serialize();


//________________________________________________________________________________//

////////////////////////////////////////////////////////////////////////////////////
//.................................Void Setup.....................................//
////////////////////////////////////////////////////////////////////////////////////
void setup(void) 
{
  piSerial.begin(115200);
  piSerial.print("dump_init");

  initial_hand_shake_sequence();

  int calibration_timeout = millis();

  set_up_imu();

  check_for_bmp_status();

  set_up_bmp();

  set_up_gps();

  

  while (((millis()-calibration_timeout) < minimum_calibration_time) || (!BMP_CONNECTED) || (!BNO_CONNECTED) || (!GPS_CONNECTED)) {
    if ((millis() - calibration_timeout) > maximum_calibration_time) {
      break; 
    }
    pull_data();

  } // while loop

    final_hand_shake_sequence();
} // void loop
  



void loop(void) {

  sample_GPS();

  /* if millis() or timer wraps around, we'll just reset it
     We don't want the timer to be bigger the clock timer on the processor. */
  if (timer > millis())
  {
    timer = millis();
  }

  /////////////////////////////////////////////////////////////////////////////////// 
  //  READ SENSORS AND SEND DATA AT 10Hz. (Every 100 milliseconds)
  ///////////////////////////////////////////////////////////////////////////////////
  if (millis() - timer > 100) 
  {
    //_____________Reset Timer______________//
    timer = millis(); // reset the timer
 
    //___________Create JSON Object__________// 
    StaticJsonDocument<500> doc; //PACKET SIZE = 550

    //___________Create JSON Arrays__________//
    JsonArray hdr = doc.createNestedArray("hdr"); //create the Json Object
    JsonArray tpa = doc.createNestedArray("tpa");
    JsonArray imu = doc.createNestedArray("imu");
    JsonArray gps = doc.createNestedArray("gps");

    tpa = fill_in_bmp_array(tpa);

    imu = fill_in_bno_array(imu);

    gps = fill_in_gps_array(gps);

    set_sensor_status_flags(gps, imu, tpa);

    hdr = fill_in_hdr_array(hdr);

    //______________Send Data______________//
    serializeJson(doc, piSerial);
    piSerial.println("");

    packetNo++;
  } // timer
} // loop

/*
 * Function Name: sample_gps() 
 * 
 * Variables: None
 * 
 * Output: None
 * 
 * Description: This function reads from the GPS registers that contiain data
 *              and tries to parse the last data string that it receives. If
 *              no data can be found, the function returns and the loop continues.
 */
void sample_GPS()
{
  GPS.read();
  if (GPS.newNMEAreceived())
  {
    // Then you parse the data that was received. See header for NMEA example.
    if (!GPS.parse(GPS.lastNMEA())) 
      return; 
  }
}

/*
 * Function Name: fill_in_bmp_array() 
 * 
 * Variables: JsonArray tpa
 * 
 * Output: JsonArray
 * 
 * Description: This function reads from the bmp sensor, adding
 *              values to the tpa json array. This is necessary due
 *              to the need for methods on the tpa object, where a pointer
 *              could not be used.
 */
JsonArray fill_in_bmp_array(JsonArray tpa)
{
  tpa.add(bmp.readTemperature());       
  tpa.add(bmp.readPressure());
  tpa.add(bmp.readAltitude(1013.25)-(*alti_offset_address+.1));

  return tpa;
}

/*
 * Function Name: fill_in_bno_array() 
 * 
 * Variables: 
 *   - name: bno type: Json Array
 * 
 * Output: JsonArray
 * 
 * Description: This function samples the IMU, creating the necessary
 *              vectors that are then used to sample the data.
 */
JsonArray fill_in_bno_array(JsonArray imu)
{
  quat = bno.getQuat();           
  vaccel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
  laccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
  angular_vel = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);

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

  return imu;
}

JsonArray fill_in_gps_array(JsonArray gps)
{
  // Only show the GPS is connected when it has valid data.
  GPS_CONNECTED = false;

  // Subtract the ground-level altitude from the GPS altitude measurements
  // to reframe measurements to calculation levels.
  if (GPS.altitude != 0 && altitude_valid == false)
    {
      *gps_alti_offset_address = GPS.altitude;
      altitude_valid = true;
    }
    gps.add(GPS.latitudeDegrees);
    gps.add(GPS.longitudeDegrees);
    gps.add(GPS.altitude - *gps_alti_offset_address);

  return gps;
}

JsonArray fill_in_hdr_array(JsonArray hdr)
{
  hdr.add(packetNo); //each packet is assigned a sequential number
  hdr.add(millis()); //creates a millisecond readout based on the Arduino's internal clock 
  hdr.add(GPS_CONNECTED);
  hdr.add(BMP_CONNECTED);
  hdr.add(BNO_CONNECTED);

  return hdr;
}

void set_sensor_status_flags(JsonArray gps, JsonArray imu, JsonArray tpa)
{
  // If longitude and latitude are non-zero, the GPS has a signal.
  if ((gps[1] != 0) && (gps[0]!= 0)) {GPS_CONNECTED = true;}
  
  // If the altitude calculation is not within expected range, the sensor is malfunctioning
  // or we have lost connection. Due to configuration, both sensors will fail in this instance.
  if ((tpa[2] < -50) || (tpa[2] > 3300)) {BMP_CONNECTED = false, BNO_CONNECTED = false;}

  // If the controller is disconnected from the sensors, all values go to 0. This means the
  // the BNO is not connected.
  if (imu[3] == 0 && imu[4] == 0 && imu[5] == 0 && imu[6] == 0)
  {
    BNO_CONNECTED = false;
  }
}

void set_up_gps()
{
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

    /*  SET UPDATE RATE: 
    For the parsing code to work nicely and have time to sort 
    thru the data, and print it out we don't suggest using 
    anything higher than 1 Hz */
    GPS.sendCommand(PMTK_SET_NMEA_UPDATE_10HZ); // 1 Hz update rate
    
    delay(1000);

    // Initialize the offset to be 0
    *gps_alti_offset_address = 0.0;
  }
} // set_up_gps

void check_for_bmp_status()
{
  uint8_t i;
  //Start and set the BMP 055..................................................
  for(i = 0; i < 3; i++)
  {
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
} // check_for_bmp_status

void set_up_bmp()
{
  // Set up BMP parameters
  if(BMP_CONNECTED){
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     /* Operating Mode. */
    Adafruit_BMP280::SAMPLING_X2,     /* Temp. oversampling */
    Adafruit_BMP280::SAMPLING_X16,    /* Pressure oversampling */
    Adafruit_BMP280::FILTER_X16,      /* Filtering. */
    Adafruit_BMP280::STANDBY_MS_500); /* Standby time. */

    *alti_offset_address = bmp.readAltitude(1013.25);
  }
} // set_up_bmp

void set_up_imu()
{
  //Start and set the BNO 055..................................................
  uint8_t i;
  for(i = 0; i < 3; i++)
  {
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

  // Needs to set a crsytal osscilator for measurements
  if(BNO_CONNECTED){
    bno.setExtCrystalUse(true);
  }
}

void final_hand_shake_sequence()
{
  for(int i = 0; i < 3; i++){
    piSerial.println("initialized");
  }

  // On command "dump", sensor suite begins sending data.
  while (1){
    while(!piSerial.available());
    if (piSerial.find("dump")){
      break;
    }
  }
}

void initial_hand_shake_sequence()
{
   while (1){
    while(!piSerial.available());
    if (piSerial.find("startup")){
      Serial.println("starting");
      break;
    }
  }
}

void pull_data(){
  
  sample_GPS();

  /* if millis() or timer wraps around, we'll just reset it
     We don't want the timer to be bigger the clock timer on the processor. */
  if (timer > millis())
  {
    timer = millis();
  }

  /////////////////////////////////////////////////////////////////////////////////// 
  //  READ SENSORS AND SEND DATA AT 10Hz. (Every 100 milliseconds)
  ///////////////////////////////////////////////////////////////////////////////////
  if (millis() - timer > 100) 
  {
    //_____________Reset Timer______________//
    timer = millis(); // reset the timer
 
    //___________Create JSON Object__________// 
    StaticJsonDocument<500> doc; //PACKET SIZE = 550

    //___________Create JSON Arrays__________//
    JsonArray hdr = doc.createNestedArray("hdr"); //create the Json Object
    JsonArray tpa = doc.createNestedArray("tpa");
    JsonArray imu = doc.createNestedArray("imu");
    JsonArray gps = doc.createNestedArray("gps");

    tpa = fill_in_bmp_array(tpa);

    imu = fill_in_bno_array(imu);

    gps = fill_in_gps_array(gps);

    set_sensor_status_flags(gps, imu, tpa);

    hdr = fill_in_hdr_array(hdr);

    packetNo++;
  } // timer
} // function
