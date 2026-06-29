from brain_client import get_memory_events
from qwen_plus import generate_script
from recap import generate_recap

def main():
    events = get_memory_events()
    script = generate_script(events)
    recap = generate_recap(script)
    with open('showrunner.private', 'w') as f:
        f.write(script)
    with open('recap.txt', 'w') as f:
        f.write(recap)

if __name__ == '__main__':
    main()
