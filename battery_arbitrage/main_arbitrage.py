#!/usr/bin/env python3

FUDGE_FACTOR = 1.0



import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from energylib import comedlib

#import battery_info
#battery_array = battery_info.get_battery_array()
#print("SOC list:", battery_array.get_all_soc())


class SystemControl():
    def __init__(self):
        pass


    def turn_off(self):
        # use wemo to turn off entire circuit
        pass


    def charge(self):
        # use switch to enable discharging of batteries to the grid
        pass


    def discharge(self):
        # use switch to charge batteries from the grid
        pass

def compare(value, thresholds, direction):
    if direction == 'less':
        return all(value < t - FUDGE_FACTOR for t in thresholds)
    elif direction == 'greater':
        return all(value > t + FUDGE_FACTOR for t in thresholds)
    else:
        raise ValueError("Direction must be 'less' or 'greater'")

#======================================
if __name__ == '__main__':
    # Measure start time
    start_time = time.time()

    syscontrol = SystemControl()
    comlib = comedlib.ComedLib()
    # Calculate and print the 24-hour median rate
    medrate, std = comlib.getMedianComedRate()
    print(f"24hr Median Rate    {medrate:.3f}c +- {std:.3f}c")

    # Calculate and print the predicted future rate
    predictrate = comlib.getPredictedRate()
    print(f"Hour Predicted Rate {predictrate:.3f}c")

    # Calculate and print the reasonable cutoff
    cutoffrate = comlib.getReasonableCutOff()
    print(f"Reasonable Cutoff   {cutoffrate:.3f}c")

    print(f"Differences: vs Median = {predictrate - medrate:.3f}, vs Cutoff = {predictrate - cutoffrate:.3f}")

    # Determine and print the house usage status based on the current rate and cutoff
    if compare(predictrate, [medrate, cutoffrate], "greater"):
        print("Status: DISCHARGE --- SEND ENERGY TO GRID")
        syscontrol.discharge()
    elif compare(predictrate, [medrate, cutoffrate], "less"):
        print("Status: CHARGE --- PULL ENERGY FROM GRID")
        syscontrol.charge()
    else:
        print("Status: OFF")å
        syscontrol.turn_off()

    # Measure end time and print run-time duration
    end_time = time.time()
    print(f"Script run time: {end_time - start_time:.2f} seconds")
