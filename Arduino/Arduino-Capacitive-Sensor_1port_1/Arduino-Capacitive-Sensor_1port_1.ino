

#include <CapacitiveSensor.h>

//CapacitiveSensor   cs_2_6 = CapacitiveSensor(2,6); // 1M resistor between pins 2 & 6, pin 6 is sensor pin, add a wire and or foil
CapacitiveSensor   cs_5_9 = CapacitiveSensor(5,9); // 1M resistor between pins 8 & 11, pin 11 is sensor pin, add a wire and or foil

void setup()                    
{
   //cs_2_6.set_CS_AutocaL_Millis(0xFFFFFFFF);// turn off autocalibrate on channel 1 - just as an example
   cs_5_9.set_CS_AutocaL_Millis(0xFFFFFFFF);

   Serial.begin(9600);
  // pinMode(7,OUTPUT);
   pinMode(12,OUTPUT);
}

void loop()                    
{
 //long sensor1 =  cs_2_6.capacitiveSensor(1);
 long sensor2 = cs_5_9.capacitiveSensor(1);

   Serial.println(sensor2);  // print sensor output 
   
   if(sensor2 >= 90)
   {
    digitalWrite(12,HIGH);
   }
   else{
    digitalWrite(12,LOW);
   }  
   
}
