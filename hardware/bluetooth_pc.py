# This project requires PyBluez
from tkinter import *
import bluetooth

#Look for all Bluetooth devices
#the computer knows about.
print("Searching for devices...")
print("")
#Create an array with all the MAC
#addresses of the detected devices
nearby_devices = bluetooth.discover_devices()
#Run through all the devices found and list their name
print("Select your device by entering its coresponding number...")
for i,device in enumerate(nearby_devices):
	print(i+1 , ": " , bluetooth.lookup_name( device ))

#Allow the user to select their Arduino
#bluetooth module. They must have paired
#it before hand.
selection = int(input("> ")) - 1
print("You have selected", bluetooth.lookup_name(nearby_devices[selection]))
bd_addr = nearby_devices[selection]

port = 1

with bluetooth.BluetoothSocket() as sock: #bluetooth.RFCOMM
    
    print("Connecting to: ", bd_addr)
    sock.connect((bd_addr, port))

    try:
        while True:
            data = sock.recv(1024)
            if not data:
                break
            print("Received: ", data)
    except:
        print("Ocurrio un error")
