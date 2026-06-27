from brain_storage import get_recent_events
import subprocess
import dashscope
import os

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

def format_time(seconds):
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"

def generate_script(limit=10):
    events = get_recent_events(limit=limit)
    prompt = "Generate a script based on the following events:\n"
    for event in events:
        prompt += f"{event['timestamp']} - {event['type']}: {event['summary']}\n"
    response = dashscope.Generation.call(
        model='qwen-turbo',
        prompt=prompt
    )
    if response.status_code == 200:
        return response.output.text
    else:
        return f"Error generating script: {response.message}"

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
