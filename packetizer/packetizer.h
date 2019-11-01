/******************************************
 * FILE:       packetizer.h
 * AUTHOR:     Zac Carico
 * LAST MOD:   Oct 3 2019
 * CREATED:    Oct 2 2019
 * 
 * SUMMARY: 
 *    A configurable and intuitive program
 *    that can send and receives packets 
 *    over serial communication. In this way,
 *    someone can use this same code on both
 *    devices that are communicating with 
 *    eachother. See comments below for more 
 *    information on how it can be configured 
 *    for various applications and platforms. 
 * ****************************************/
#include <stdint.h>
#include <stdio.h>

/*SETTINGS FOR PACKETS*/
#define MAX_DATA_SIZE 5 // In bytes. Change this to increase the max amount of data you can send
#define BAUD 9600       // Change this to change the baudrate of the communication
#define SOF_CODE 0xC0DE // Can be any size and value. Default value is "0xCODE", very creative
#define EOF_CODE 0xEDOC // Can be any size and value. Default value is "0xEDOC", even more creative
#define TIME_STAMP_SIZE 2 //How many bytes for the timestamp

// #define VERBOSE

/*DEFINES DEPENDANT ON PACKET SETTINGS*/

//These sizes are determined by the size of the SOF/EOF code, and
//  while it does return type size_t, it is compatable with int.
#define SOF_SIZE (sizeof SOF_CODE) / 2 
#define EOF_SIZE (sizeof EOF_CODE) / 2 


/* *
 * SETTINGS FOR DEVICES
 * 
 * This can be used by compiling with '-D <OPTION_NAME>',
 * or by just adding the define below this block.
 * 
 * If the device you're using is not located in the list, 
 * feel free to add it, and send a commit. This way others 
 * can also use this too.
 * */
#define PC

#ifdef PI //Define this when compiling on the Pi
    #include <wiringSerial.h>
    
    // Needed for wiring pi library
    int fd;
    void set_fd(int x) { fd = x; }

    #define HANDSHAKE "GIME" //Give Me
    #define SEND(x) serialPutchar(fd, (unsigned char) x)
    #define READ serialGetchar(fd)
    #define FLUSH serialFlush(fd)
    #define AVAILABLE serialDataAvail(fd)
    #define DEBUG(x) printf(x)
#else
    #ifdef PC //Define this when compiling on any other computer
        #define HANDSHAKE "WHY?"
        #define SEND(x) printf("Sending %x\n", x)
        #define READ 0; printf("Reading Data\n")
        #define FLUSH printf("Flushing Buffers\n")
        #define AVAILABLE 1; printf("Checking availability\n")
        #define DEBUG(x) printf(x) //Comment this out if it is not needed
    #else //No defines means that it is using the Teensy
        #define HANDSHAKE "FINE" 
        #define SEND(x) Serial1.write(x)
        #define READ Serial1.read()
        #define FLUSH Serial1.flush()
        #define AVAILABLE Serial1.available()
        #define DEBUG(x) Serial1.print(x)
    #endif
#endif

/*Custom Types*/

/* *
 * Modify this to meet your needs. Be sure to change functions as necessary.
 * 
 * By default, the "EOF", or "End of Frame" is a CRC check byte. This can be 
 *      changed to another check algorithm, and/or add an "EOF".
 * */
typedef struct{
    uint8_t SOF[SOF_SIZE];                  //Start of frame
    uint8_t HEARTBEAT;                      //Frame sequence number
    uint8_t CMD;                            //Command
    uint8_t DATA[MAX_DATA_SIZE];            //Data to be sent
    uint8_t TIME_STAMP[TIME_STAMP_SIZE];    //Time that data was pulled (relative to sender)
    uint8_t CRC[2];                         //Check
} Packetizer;

/* *
 * Change "PCKT_TYP_X" to the number of bytes of data that will come in.
 * 
 * EX: If "PCKT_TYP_1" sends a 2byte number from sensor A, set it equal to 2
 *        to signify 2 bytes
 *     
 *     If "PCKT_TYP_2" sends a 2byte number from sensor A and a 3 byte number 
 *        from sensor B, set it equal to 5 to signify 5 bytes
 * */
typedef enum{
    INIT        = 0,                //For handshake
    SEND_DATA   = MAX_DATA_SIZE,    //Send all data
    PCKT_TYP_1  = 1,                //Send 1 data item
    PCKT_TYP_2  = 2,                //Send 2 data items
    PCKT_TYP_3  = 3,                //Send 3 data items
    PCKT_TYP_4  = 4                 //Send 4 data items
} COMMANDS;

/* *
 * Used by "receive_packet()". If you want to add to this list to meet 
 *      the needs of your packet, be sure to change the state machine 
 *      in "receive_packet()".
 * */
typedef enum{
    SOF,
    HEARTBEAT,
    CMD,
    DATA,
    TIME_STAMP,
    CRC, 
    DONE
} Packet_States;

/*Functions*/
void send_handshake();
void calc_crc(Packetizer *packet);
void send_packet(Packetizer *packet);
void empty_packet(Packetizer *packet);
uint8_t receive_packet(Packetizer *packet);


/* *
 * code needed by Cython
 * */
Packetizer gPacket;

Packetizer send(Packetizer packet)
{
    send_packet(&packet);
    return packet;
}

Packetizer receive(Packetizer packet)
{
    receive_packet(&packet);
    return packet;
}

Packetizer crc(Packetizer packet)
{
    calc_crc(&packet);
    return packet;
}
