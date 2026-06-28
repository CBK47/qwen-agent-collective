from app import db
from models import Device
from app.brain_client import BrainClient

class DeviceRegistry:
    def __init__(self):
        self.brain_client = BrainClient()
        device_registry = self.brain_client.process("get device registry", None, None)

        for device_name, actions in device_registry.items():
            for action_keyword, action in actions.items():
                new_device = Device(device_name=device_name, action_keyword=action_keyword, action=action)
                db.session.add(new_device)
        db.session.commit()

    def parse_command(self, input_data):
        if isinstance(input_data, dict):
            text = input_data.get('text', '')
            image = input_data.get('image')
            audio = input_data.get('audio')
        elif isinstance(input_data, str):
            text = input_data
            image = None
            audio = None
        else:
            return None

        return self.brain_client.process(text, image, audio)

    def process_manual_input(self, manual_input, current_command):
        device_name = current_command['device']
        devices = Device.query.filter_by(device_name=device_name).all()
        manual_input_lower = manual_input.lower()
        for device in devices:
            if device.action_keyword in manual_input_lower:
                return {
                    'device': device_name,
                    'action': device.action,
                    'params': current_command.get('params', {})
                }
        return None
