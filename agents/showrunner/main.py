from brain_client import get_memory_events, send_to_webui
from qwen_plus import generate_script
from recap import generate_recap

def main():
    events = get_memory_events()
    script = generate_script(events)
    recap = generate_recap(script)
    send_to_webui(script, recap)

if __name__ == '__main__':
    main()
