class DeviceRegistry:
    def __init__(self):
        self.devices = {
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

    def parse_command(self, text):
        text = text.lower()
        for device_name, actions in self.devices.items():
            if device_name in text:
                for action_keyword, action in actions.items():
                    if action_keyword in text:
                        return {
                            'device': device_name,
                            'action': action,
                            'params': {}
                        }
        return None
