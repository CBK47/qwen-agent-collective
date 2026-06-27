from brain_storage import get_recent_events

def generate_script(limit=10):
    events = get_recent_events(limit=limit)
    script_lines = []
    for event in events:
        script_lines.append(f"{event['timestamp']} - {event['type']}: {event['summary']}")
    return "\n".join(script_lines)
