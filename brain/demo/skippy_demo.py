from skippy_concierge.device_handler import DeviceHandler

def main():
    device = DeviceHandler(device_id="demo_device")
    device.connect()
    print("Connected to device")
    device.turn_on()
    print("Device turned on")
    status = device.get_status()
    print(f"Current status: {status}")
    device.set_temperature(72)
    print("Temperature set to 72 degrees")
    status = device.get_status()
    print(f"Updated status: {status}")
    device.turn_off()
    print("Device turned off")

if __name__ == "__main__":
    main()
