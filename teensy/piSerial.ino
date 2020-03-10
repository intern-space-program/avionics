//////////////////////////////////ISP_Avionics//////////////////////////////////
/*  Created: 3.10.20 by Blake Shaffer
 *     Name: 
 * Function: 
 *    Notes: 
 *  Updates: 
 *
 */
///////////////////////////////////Libraries!///////////////////////////////////

/////////////////////////////Variables and #Defines/////////////////////////////
#define piSerial Serial1; //port for pi0 communication

bool SEND_DATA = false;   //flag to know when to send data to raspi

//////////////////////////////////////MAIN//////////////////////////////////////
void setup(){
  piSerial.begin(115200);   //begin serial comm with raspi (Rx=0, Tx=1)
  piSerial.print("Communication initialization...");  //print message to raspi

  //initial_handshake();
}

void loop(){
}

///////////////////////////////////Functions!///////////////////////////////////

void
initial_handshake(){
   
   /*
   while (1){
    while( !piSerial.available() );
    if (piSerial.find("startup")){
      delay(100);
      piSerial.println("starting");
      break;
    }
  }
  */
}



/*******************************************************************************
*        Name: 
* Description: 
*       Input: 
*  Out/Modify: 
*******************************************************************************/

//////////////////////////////////ISP_Avionics//////////////////////////////////
