from app import db
from models import Device

class DeviceRegistry:
    def __init__(self):
        sample_devices = {
            'lights': {
                'on': 'turn_on',
                'off': 'turn_off',
                'dim': 'dim'
            },
            'thermostat': {
                'set temperature': 'set_temp',
                'increase': 'increase_temp',
                'decrease': 'decrease_temp'
            },
            'tv': {
                'on': 'power_on',
                'off': 'power_off',
                'volume up': 'volume_up',
                'volume down': 'volume_down'
            }
        }

        for device_name, actions in sample_devices.items():
            for action_keyword, action in actions.items():
                new_device = Device(device_name=device_name, action_keyword=action_keyword, action=action)
                db.session.add(new_device)
        db.session.commit()

    def parse_command(self, text):
        text = text.lower()
        all_devices = Device.query.all()
        for device in all_devices:
            if device.device_name in text:
                if device.action_keyword in text:
                    return {
                        'device': device.device_name,
                        'action': device.action,
                        'params': {}
                    }
        return None
