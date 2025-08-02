#!/usr/bin/env python3

import time
import yaml
from bluepy.btle import Peripheral, DefaultDelegate

debug = True

QUERY_BASIC = b"\xdd\xa5\x03\x00\xff\xfd\x77"
QUERY_CELLS = b"\xdd\xa5\x04\x00\xff\xfc\x77"
SERVICE_UUID = 0xff00
CHAR_UUID = 0xff02

with open("arbitrage_config.yml", "r") as f:
    config = yaml.safe_load(f)

battery_macs = config.get("ecoworthy_batteries", [])

class BatteryData(DefaultDelegate):
    def __init__(self, mac):
        super().__init__()
        self.mac = mac
        self.buffer = b""
        self.last_packet = None
        self.periph = Peripheral(self.mac)
        self.periph.withDelegate(self)
        self.char = self.periph.getServiceByUUID(SERVICE_UUID).getCharacteristics(CHAR_UUID)[0]
        #self._prime_connection()

    def handleNotification(self, cHandle, data):
        if debug:
            print(f"[{self.mac}] Notification: {data.hex()}")
        self.buffer += data
        if debug:
            print(f"[{self.mac}] Buffer: {self.buffer.hex()}")
        if self.buffer.endswith(b'\x77'):
            self.last_packet = self.buffer
            if debug:
                print(f"[{self.mac}] Full packet: {self.last_packet.hex()}")
            self.buffer = b""

    def _prime_connection(self):
        if debug:
            print(f"[{self.mac}] Priming BLE connection with QUERY_CELLS...")
        self._query(QUERY_CELLS)

    def _query(self, command):
        if debug:
            print(f"[{self.mac}] Sending command: {command.hex()}")
        self.buffer = b""
        self.last_packet = None
        self.char.write(command, withResponse=True)

        timeout = 10 # seconds
        step_size = 0.2 # seconds
        start = time.time()
        while time.time() - start < timeout:
            if self.periph.waitForNotifications(step_size):
                if self.last_packet:
                    break
        if debug:
            if self.last_packet:
                print(f"[{self.mac}] Final packet after query: {self.last_packet.hex()}")
            else:
                print(f"[{self.mac}] No packet received after query.")
        return self.last_packet

    def get_basic_info(self):
        if debug:
            print(f"[{self.mac}] Requesting basic info...")
        raw = self._query(QUERY_BASIC)
        if not raw:
            raise ValueError(f"[{self.mac}] No response received (None)")
        if debug:
            print(f"[{self.mac}] Raw basic response length: {len(raw)}")
        if len(raw) < 30:
            print(f"[{self.mac}] Raw response too short: {raw.hex()}")
            raise ValueError(f"[{self.mac}] No valid basic response")

        voltage = int.from_bytes(raw[4:6], "big") / 100
        current = int.from_bytes(raw[6:8], "big", signed=True) / 100
        ah_rem = int.from_bytes(raw[8:10], "big") / 100
        ah_max = int.from_bytes(raw[10:12], "big") / 100
        soc = 100 * ah_rem / ah_max if ah_max else None
        temp = (int.from_bytes(raw[27:29], "big") - 2731) / 10
        return {
            "voltage": round(voltage, 2),
            "current": round(current, 2),
            "soc": round(soc, 2) if soc else None,
            "temperature": round(temp, 1)
        }

    def get_cell_voltages(self):
        raw = self._query(QUERY_CELLS)
        if not raw or len(raw) < 8:
            raise ValueError(f"[{self.mac}] No valid cell response")
        num_cells = raw[2] // 2
        cells = [
            int.from_bytes(raw[4 + 2 * i:6 + 2 * i], "big") / 1000
            for i in range(num_cells)
        ]
        return [round(v, 3) for v in cells]

    def get_all_data(self):
        info = self.get_basic_info()
        cells = self.get_cell_voltages()
        info["mac"] = self.mac
        info["cell_voltages"] = cells
        return info

    def close(self):
        self.periph.disconnect()


class BatteryArrayData:
    def __init__(self, mac_list):
        self.mac_list = mac_list

    def get_all_soc(self):
        results = []
        socs = []
        for mac in self.mac_list:
            try:
                b = BatteryData(mac)
                info = b.get_basic_info()
                results.append({"mac": mac, "soc": info["soc"]})
                socs.append(info["soc"])
                b.close()
            except Exception as e:
                print({"mac": mac, "error": str(e)})
        return socs


    def get_all_data(self):
        results = []
        for mac in self.mac_list:
            try:
                b = BatteryData(mac)
                data = b.get_all_data()
                results.append(data)
                b.close()
            except Exception as e:
                results.append({"mac": mac, "error": str(e)})
        return results


def get_battery_array():
    battery_array = BatteryArrayData(battery_macs)
    return battery_array


if __name__ == "__main__":
    battery_array = get_battery_array()
    results = battery_array.get_all_soc()
    print(results)
    results = battery_array.get_all_data()
    for data in results:
        print(f"\nBattery {data['mac']}")
        if "error" in data:
            print("  Error:", data["error"])
            continue
        print(f"  Voltage:     {data['voltage']} V")
        print(f"  Current:     {data['current']} A")
        print(f"  SOC:         {data['soc']} %")
        print(f"  Temp:        {data['temperature']} °C")
        for i, v in enumerate(data['cell_voltages']):
            print(f"  Cell {i + 1}: {v:.3f} V")

