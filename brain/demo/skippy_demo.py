import argparse
from skippy_concierge.device_handler import DeviceHandler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_events', type=int, default=1, help='Number of demo events to run')
    args = parser.parse_args()

    device = DeviceHandler(device_id="demo_device")
    device.connect()
    print("Connected to device")
    for _ in range(args.num_events):
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
