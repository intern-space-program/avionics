/******************************************
 * FILE:       conversion.h
 * AUTHOR:     Zac Carico
 * LAST MOD:   Oct 26 2019
 * CREATED:    Oct 26 2019
 * 
 * SUMMARY: 
 *    Converts various data types into an 
 *    array of bytes.
 * ****************************************/

#include <stdint.h>

template <class t>
void convert(t din, uint8_t *dout);
