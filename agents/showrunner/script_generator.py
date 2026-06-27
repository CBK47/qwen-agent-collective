from brain_storage import get_recent_events
import subprocess

def format_time(seconds):
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"

def generate_script(limit=10):
    events = get_recent_events(limit=limit)
    script_lines = []
    for event in events:
        script_lines.append(f"{event['timestamp']} - {event['type']}: {event['summary']}")
    return "\n".join(script_lines)

def render_video(script, resolution="1280x720", duration=5, style="font=Arial:fontsize=24:fontcolor=white"):
    lines = script.split('\n')
    srt_content = []
    for i, line in enumerate(lines):
        start = i * duration
        end = (i + 1) * duration
        srt_content.append(str(i+1))
        srt_content.append(f"{format_time(start)} --> {format_time(end)}")
        srt_content.append(line)
        srt_content.append('')
    srt_text = "\n".join(srt_content)
    with open('script.srt', 'w') as f:
        f.write(srt_text)
    total_duration = len(lines) * duration
    command = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=c=black:s={resolution}:d={total_duration}',
        '-vf', f'subtitles=script.srt:{style}',
        'output.mp4'
    ]
    subprocess.run(command)
