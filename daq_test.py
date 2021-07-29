from AntCamHW.daq_do.daq_do_dev import DAQSimpleDOTask
from time import sleep

# initiate all the odor solenoids
odor0 = DAQSimpleDOTask('Dev3/port0/line0')
clean0 = DAQSimpleDOTask('Dev3/port0/line1')
odor1 = DAQSimpleDOTask('Dev3/port0/line2')
clean1 = DAQSimpleDOTask('Dev3/port0/line3')
odor2 = DAQSimpleDOTask('Dev3/port0/line4')
clean2 = DAQSimpleDOTask('Dev3/port0/line5')
odor3 = DAQSimpleDOTask('Dev3/port0/line6')
clean3 = DAQSimpleDOTask('Dev3/port0/line7')
odor4 = DAQSimpleDOTask('Dev3/port1/line0')
clean4 = DAQSimpleDOTask('Dev3/port1/line1')
odor5 = DAQSimpleDOTask('Dev3/port1/line2')
clean5 = DAQSimpleDOTask('Dev3/port1/line3')
odor6 = DAQSimpleDOTask('Dev3/port1/line4')
clean6 = DAQSimpleDOTask('Dev3/port1/line5')
odor7 = DAQSimpleDOTask('Dev3/port1/line6')
clean7 = DAQSimpleDOTask('Dev3/port1/line7')

# set the channel to low
odor0.low()
odor1.low()
odor2.low()
odor3.low()
odor6.low()
odor7.low()
clean0.low()
clean1.low()
clean2.low() 
clean3.low()
clean6.low()
clean7.low()

# testing
clean4.high() # turn on clean odor
odor4.low() # turn off odor 4

clean5.high()
odor5.low()

# closing program
odor0.close()
odor1.close()
odor2.close()
odor3.close()
odor4.close()
odor5.close()
odor6.close()
odor7.close()
clean0.close()
clean1.close()
clean2.close()
clean3.close()
clean4.close()
clean5.close()
clean6.close()
clean7.close()

# example program of delivering water
water = DAQSimpleDOTask('Dev3/port2/line0')
numtrials = 80
water.low()

for t in range(1,numtrials):
    sleep(3)
    water.high()
    sleep(0.25)
    water.low()

water.close()