from brain_storage import get_recent_events

def generate_script():
    events = get_recent_events(limit=10)
    script_lines = []
    for event in events:
        script_lines.append(f"{event['timestamp']} - {event['type']}: {event['summary']}")
    return "\n".join(script_lines)
