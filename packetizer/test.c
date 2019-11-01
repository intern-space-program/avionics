#include <stdio.h>
#include "packetizer.h"

int main(void)
{
   Packetizer packet;
   char run = 'y';
   uint8_t cmd = 0x00;
   uint8_t data[MAX_DATA_SIZE];
   uint8_t time[2] = {0xF0, 0x0D};

   send_handshake();

   while(run == 'y')
   {
      printf("Want to send packet? [y/n] ");
      scanf("%c", &run);

      printf("Enter cmd: ");
      scanf("%x", &packet.CMD);

      for(uint8_t i = 0; i < MAX_DATA_SIZE; i++)
      {
         printf("Enter a byte of data: ");
         scanf("%x", &packet.DATA[i]);
      }
      packet.TIME_STAMP[0] = time[0];
      packet.TIME_STAMP[1] = time[1];

      send_packet(&packet);
      // empty_packet(&packet);
      // receive_packet(&packet);
   }

   return 0;
}