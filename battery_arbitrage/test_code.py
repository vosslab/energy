#!/usr/bin/env python3

import yaml
import time
from bluepy.btle import Peripheral, DefaultDelegate

# based on https://github.com/mike805/eco-worthy-battery-logger/blob/main/ewbatlog.py

CONFIG_FILE = "arbitrage_config.yml"
SERVICE_UUID = 0xff00
CHAR_UUID = 0xff02
QUERY_BASIC = b'\xdd\xa5\x03\x00\xff\xfd\x77'
QUERY_CELLS = b'\xdd\xa5\x04\x00\xff\xfc\x77'

class BatteryDelegate(DefaultDelegate):
    def __init__(self):
        super().__init__()
        self.buffer = b""
        self.cell_voltages = []

    def handleNotification(self, cHandle, data):
        print(f"Notification: {data.hex()}")
        self.buffer += data
        if self.buffer.endswith(b'\x77'):
            print(f"Full packet received: {self.buffer.hex()}")
            self.process_packet(self.buffer)
            self.buffer = b""

    def process_packet(self, pkt):
        print(f"Processing packet: {pkt.hex()}")
        if pkt[0:2] == b'\xdd\x03':
            # parse basic status
            voltage = int.from_bytes(pkt[4:6], "big") / 100
            current = int.from_bytes(pkt[6:8], "big", signed=True) / 100
            ah_rem = int.from_bytes(pkt[8:10], "big") / 100
            ah_max = int.from_bytes(pkt[10:12], "big") / 100
            soc = 100 * ah_rem / ah_max if ah_max else None
            temp = (int.from_bytes(pkt[27:29], "big") - 2731) / 10

            print(f"  Voltage:     {voltage:.2f} V")
            print(f"  Current:     {current:.2f} A")
            print(f"  SOC:         {soc:.2f} %")
            print(f"  Temp:        {temp:.1f} °C")

        elif pkt[0:2] == b'\xdd\x04':
            raw_cells = pkt[4:-3]
            self.cell_voltages = [
                int.from_bytes(raw_cells[i:i+2], 'big') / 1000
                for i in range(0, len(raw_cells), 2)
            ]
            for idx, v in enumerate(self.cell_voltages):
                print(f"  Cell {idx + 1}: {v:.3f} V")
        else:
            print("  Unknown or unhandled packet:", pkt.hex())

def _query(dev, delegate, char, command, timeout=5, step=0.2):
    delegate.buffer = b""
    char.write(command, withResponse=True)
    start = time.time()
    while time.time() - start < timeout:
        if dev.waitForNotifications(step):
            if delegate.buffer.endswith(b'\x77'):
                return delegate.buffer
    print("  Warning: No full packet received.")
    return None

def query_battery(mac):
    print(f"\nConnecting to {mac}")
    dev = Peripheral(mac)
    delegate = BatteryDelegate()
    time.sleep(1.0)

    dev.withDelegate(delegate)
    time.sleep(0.5)

    char = dev.getServiceByUUID(SERVICE_UUID).getCharacteristics(CHAR_UUID)[0]
    time.sleep(0.5)

    print("\nSending basic query (priming)... expected fail")
    _query(dev, delegate, char, QUERY_BASIC)

    print("\nSending cell voltage query...")
    _query(dev, delegate, char, QUERY_CELLS)

    print("\nSending basic query...")
    _query(dev, delegate, char, QUERY_BASIC)

    print("\nSending basic query...")
    _query(dev, delegate, char, QUERY_BASIC)

    print("\nSending cell voltage query...")
    _query(dev, delegate, char, QUERY_CELLS)

    dev.disconnect()

# Load config
with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

batteries = config.get("ecoworthy_batteries", [])
print("Batteries:", batteries)

for mac in batteries:
    query_battery(mac)

