#include <CapacitiveSensor.h>

CapacitiveSensor   cs_2_6 = CapacitiveSensor(2,6); // 1M resistor between pins 2 & 6, pin 6 is sensor pin, add a wire and or foil
CapacitiveSensor   cs_8_11 = CapacitiveSensor(8,11); // 1M resistor between pins 8 & 11, pin 11 is sensor pin, add a wire and or foil

void setup()                    
{
   cs_2_6.set_CS_AutocaL_Millis(0xFFFFFFFF);// turn off autocalibrate on channel 1 - just as an example
   Serial.begin(9600);
   pinMode(7,OUTPUT);
   pinMode(12,OUTPUT);
}

void loop()                    
{
 long sensor1 =  cs_2_6.capacitiveSensor(50);
 long sensor2 = cs_8_11.capacitiveSensor(50);

    Serial.println(sensor1);  // print sensor output 
   if(sensor1 >= 70)
   {
    digitalWrite(7,HIGH);
   }
   else{
    digitalWrite(7,LOW);
   }

   if(sensor2 >= 70)
   {
    digitalWrite(12,HIGH);
   }
   else{
    digitalWrite(12,LOW);
   }  
}
