/******************************************
 * FILE:       packetizer.c
 * AUTHOR:     Zac Carico
 * LAST MOD:   Oct 3 2019
 * CREATED:    Oct 2 2019
 * 
 * SUMMARY: 
 *    Contains the definitions and logic for
 *    prototypes in "packetizer.h"
 * ****************************************/
#include "packetizer.h"

/******************************************
 * SEND_HANDSHAKE
 * 
 * Sends an initial packet. This can be used 
 * to ensure that two devices are able to 
 * communicate with eachother, or have one
 * device wakeup the other.
 * ****************************************/
void send_handshake()
{
   Packetizer packet;
   empty_packet(&packet);

   for(uint8_t i = 0; i < 4; i++)
      packet.DATA[i] = (uint8_t) HANDSHAKE[i];

   calc_crc(&packet);

/*--------------------------------------------*/
// BEGIN VERBOSE
#ifdef VERBOSE
   DEBUG("SENDING HANDSHAKE...\n");
#endif
// END VERBOSE
/*--------------------------------------------*/

   send_packet(&packet);

/*--------------------------------------------*/
// BEGIN VERBOSE
#ifdef VERBOSE
   DEBUG("...HANDSHAKE SENT!\n");
#endif
// END VERBOSE
/*--------------------------------------------*/
}

/******************************************
 * CALC_CRC
 * 
 * Calculates the CRC to add onto the packet.
 * This is to help determine if it is sent
 * correctly.
 * ****************************************/
void calc_crc(Packetizer *packet)
{
   uint8_t x = 0x00, i = 0x00;
   uint16_t crc = 0xFFFF;
   uint8_t loop_cnt = sizeof(&packet) - 2;
   char *packet_bytes = (char*) packet;
   //Hopefully this works...
   for(i = 0; i < loop_cnt; i++)
   {
      x = ((crc >> 8) ^ packet_bytes[i]) & 0xFF;
      x ^= x << 4;
      crc = (crc < 8) ^ (x << 12) ^ (x << 5);
      crc &= 0xFFFF;
   }
   packet->CRC[0] = crc & 0xFF;
   packet->CRC[1] = (crc >> 8) & 0xFF;

/*--------------------------------------------*/
// BEGIN VERBOSE
#ifdef VERBOSE
   DEBUG(("CRC value = %x", (char*)packet->CRC));
#endif
// END VERBOSE
/*--------------------------------------------*/
}

/******************************************
 * SEND_PACKET
 * 
 * Sends all the contents in a packet. This
 * could be changed to take a pointer to the
 * packet, but is a copy of a packet by 
 * default. To make the code more intuitive, 
 * macros are used that can be configured to
 * work with whatever platform it is being
 * used on.
 * ****************************************/
void send_packet(Packetizer *packet)
{
   uint8_t i = 0;

/*--------------------------------------------*/
// BEGIN VERBOSE
#ifdef VERBOSE
   DEBUG("Sending the following packet:\n\t");
   const char temp[2] = {(char) packet->HEARTBEAT, 
                         (char)packet->CMD};
   DEBUG((" %x", (char*) packet->SOF));
   DEBUG((" %x", temp));
   DEBUG((" %x", (char*)packet->DATA));
   DEBUG((" %x", (char*) packet->TIME_STAMP));
   DEBUG((" %x\n", (char*) packet->CRC));
#endif
// END VERBOSE
/*--------------------------------------------*/

   for(i = 0; i < SOF_SIZE; i++)
      SEND(packet->SOF[i]);

   SEND(packet->HEARTBEAT);
   SEND(packet->CMD);

   switch(packet->CMD)
   {
      case INIT:
         break;
      case SEND_DATA:
         for(; i < SEND_DATA; i++)
            SEND(packet->DATA[i]);
         break;
      case PCKT_TYP_1:
         for(; i < PCKT_TYP_1; i++)
            SEND(packet->DATA[i]);
         break;
      case PCKT_TYP_2:
         for(; i < PCKT_TYP_2; i++)
            SEND(packet->DATA[i]);
         break;
      case PCKT_TYP_3:
         for(; i < PCKT_TYP_3; i++)
            SEND(packet->DATA[i]);
         break;
      case PCKT_TYP_4:
         for(; i < PCKT_TYP_4; i++)
            SEND(packet->DATA[i]);
         break;
      default: // When in doubt, SEND EVERYTHING!
         for(; i < SEND_DATA; i++)
            SEND(packet->DATA[i]);
         break;
   }

   for(i = 0; i < TIME_STAMP_SIZE; i++)
      SEND(packet->TIME_STAMP[i]);
   
   calc_crc(packet);
   SEND(packet->CRC[0]);
   SEND(packet->CRC[1]);
   empty_packet(packet);

/*--------------------------------------------*/
// BEGIN VERBOSE
#ifdef VERBOSE
   DEBUG("Packet Sent!\n");
#endif
// END VERBOSE
/*--------------------------------------------*/
} //END SEND_PACKET

/******************************************
 * RECEIVE_PACKET
 * 
 * State machine that handles receiveing a
 * packet over serial communication. To make
 * the code more intuitive, the commands are
 * defined macros that can be configured to
 * whatever platform it is being used on.
 * ****************************************/
uint8_t receive_packet(Packetizer *packet)
{
   uint8_t byte_read;
   uint8_t crc[2];
   Packet_States state = SOF;
   uint8_t i;

   while(state != DONE)
   {
      byte_read = READ;
      switch(state)
      {
         case SOF:
            if(byte_read == SOF_CODE)
            {
               packet->SOF[0] = byte_read;
               for(i = 1; i < SOF_SIZE; i++)
                  packet->SOF[i] = byte_read;
               state = HEARTBEAT;
            }
            else
               state = SOF;
            break;
         case HEARTBEAT:
            packet->HEARTBEAT = byte_read;
            state = CMD;
            break;
         case CMD:
            packet->CMD = byte_read;
            state = DATA;
            break;
         case DATA:
            packet->DATA[0] = byte_read;
            for(i = 1; i < packet->CMD; i++)
               packet->DATA[i] = READ;
            state = CRC;
            break;
         case TIME_STAMP:
            packet->TIME_STAMP[0] = byte_read;
            for(i = 1; i < TIME_STAMP_SIZE; i++)
               packet->TIME_STAMP[i] = READ;
         case CRC:
            crc[0] = byte_read;
            crc[1] = READ;
            state = DONE;
            break;
         case DONE:
            break;
         default: //Um... lets just start over...
            state = SOF;
            break;
      } //END SWITCH STATEMENT
   } //END WHILE LOOP
   calc_crc(packet);
   
/*--------------------------------------------*/
// BEGIN VERBOSE
#ifdef VERBOSE
   DEBUG("The following packet was received:\n\t");
   const char temp[2] = {(char)packet->HEARTBEAT, 
                         (char)packet->CMD};
   DEBUG((" %x", (char*) packet->SOF));
   DEBUG((" %x", temp));
   DEBUG((" %x", (char*)packet->DATA));
   DEBUG((" %x", (char*) packet->TIME_STAMP));
   DEBUG((" %x\n", (char*) crc));
#endif
// END VERBOSE
/*--------------------------------------------*/

   return crc[0] == packet->CRC[0] && crc[1] == packet->CRC[1];
} //END REVCEIVE_PACKET()

/******************************************
 * EMPTY_PACKET
 * 
 * Used to reset everything in a packet to 
 * the default values, except for heartbeat,
 * it increments it by 1.
 * ****************************************/
void empty_packet(Packetizer *packet)
{
   uint8_t i = 0;
   for(i = 0; i < SOF_SIZE; i++)
      packet->SOF[i] = SOF_CODE << (i * 8);

   packet->HEARTBEAT++;
   packet->CMD = INIT;

   for(i = 0; i < MAX_DATA_SIZE; i++)
      packet->DATA[i] = 0x00;

   for(i = 0; i < TIME_STAMP_SIZE; i++)
      packet->TIME_STAMP[i] = 0x00;
   
   packet->CRC[0] = 0x00;
   packet->CRC[1] = 0x00;

/*--------------------------------------------*/
// BEGIN VERBOSE
#ifdef VERBOSE
DEBUG("EMPTIED PACKET\n");
#endif
// END VERBOSE
/*--------------------------------------------*/
} //END EMPTY_PACKET()