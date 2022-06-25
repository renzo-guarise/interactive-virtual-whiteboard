//Include the module so we don't
//have to use the default Serial
//so the Arduino can be plugged in
//to a computer and still use bluetooth
#include <SoftwareSerial.h>

//Define the pins used for receiving
//and transmitting information via Bluetooth
const int rxpin = 2;
const int txpin = 3;

//Variable to store input value
//initialized with arbitrary value
char k = 'A';

//Connect the Bluetooth module
SoftwareSerial bluetooth(rxpin, txpin);

const int button1pin = 8;
const int button2pin = 9;
const int button3pin = 10;

void setup()
{
  //Set the lightbulb pin to put power out
  pinMode(button1pin, INPUT_PULLUP);
  pinMode(button2pin, INPUT_PULLUP);
  pinMode(button3pin, INPUT_PULLUP);
  
  //Initialize Serial for debugging purposes
  Serial.begin(9600);
  Serial.println("Serial ready");
  
  //Initialize the bluetooth
  bluetooth.begin(9600);
  bluetooth.println("Bluetooth ready");
  Serial.println("Bluetooth ready");
}

void loop()
{
  //Check for new data
  if (bluetooth.available()){
    Serial.write(bluetooth.read());
  }
    
  if (Serial.available()){
    bluetooth.write(Serial.read());
  }
  

  // Read buttons and send if someone is pressed
  int button1state = digitalRead(button1pin);
  if (button1state == LOW) {
    Serial.println("1");
    bluetooth.println("1");
  } else {
    //digitalWrite(13, HIGH);
  }
  
  int button2state = digitalRead(button2pin);
  if (button2state == LOW) {
    Serial.println("2");
    bluetooth.println("2");
  } else {
    //digitalWrite(13, HIGH);
  }
  
  int button3state = digitalRead(button3pin);
  if (button3state == LOW) {
    Serial.println("3");
    bluetooth.println("3");
  } else {
    //digitalWrite(13, HIGH);
  }
  
  /*
  //Turn on the light if transmitted data is H
  if( k == 'H' ){
    digitalWrite(7, HIGH);
  }
  //Turn off the light if transmitted data is L
  else if( k == 'L') {
    digitalWrite(7, LOW);
  }
  // */
  
  //Wait ten milliseconds to decrease unnecessary hardware strain
   delay(10);
}
