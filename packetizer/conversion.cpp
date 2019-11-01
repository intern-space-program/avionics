/******************************************
 * FILE:       conversion.cpp
 * AUTHOR:     Zac Carico
 * LAST MOD:   Oct 26 2019
 * CREATED:    Oct 26 2019
 * 
 * SUMMARY: 
 *    Contains the definitions and logic for
 *    prototypes in "conversion.h"
 * ****************************************/

#include "conversion.h"

template <class t>
void convertTo(t din, uint8_t *dout)
{
   uint8_t size = sizeof(din);
   dout = new uint8_t[size];
   memcpy(dout, (unsigned char*) (&din), size);
}

template <class t>
t convertFrom(uint8_t *din)
{
   
}