#!/usr/bin/env python3

import battery_info

battery_array = battery_info.get_battery_array()
print("SOC list:", battery_array.get_all_soc())

results = battery_array.get_all_data()
for data in results:
    print(f"\nBattery {data['mac']}")
    if "error" in data:
        print("  Error:", data["error"])
        continue
    print(f"  Voltage:     {data['voltage']} V")
    print(f"  Current:     {data['current']} A")
    print(f"  SOC:         {data['soc']} %")
    print(f"  Temp:        {data['temperature']:.1f} °C")
    for i, v in enumerate(data['cell_voltages']):
        print(f"  Cell {i + 1}:     {v:.3f} main_arbitrage.py V")

