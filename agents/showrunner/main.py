from brain_client import get_memory_events
from qwen_plus import generate_script

def main():
    events = get_memory_events()
    script = generate_script(events)
    with open('showrunner.private', 'w') as f:
        f.write(script)

if __name__ == '__main__':
    main()
