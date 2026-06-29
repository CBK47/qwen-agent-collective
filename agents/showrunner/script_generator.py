from brain_client import get_memory_events
import subprocess
import dashscope
import os

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

def format_time(seconds: float) -> str:
    """Converts seconds to a formatted time string in HH:MM:SS,mmm format.

    Args:
        seconds: The total number of seconds to format.

    Returns:
        A string in the format HH:MM:SS,mmm.
    """
    total_seconds = int(seconds)
    milliseconds = int((seconds - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def generate_script(limit: int = 10) -> str:
    """Generates a script based on memory events.

    Args:
        limit: The maximum number of events to retrieve.

    Returns:
        The generated script text or an error message if the API call fails.
    """
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    if not dashscope.api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    events = get_memory_events(limit=limit)
    events.sort(key=lambda x: x['timestamp'])
    prompt = "Generate a script based on the following events:\n"
    for event in events:
        prompt += f"{format_time(event['timestamp'])} - {event['type']}: {event['summary']}\n"
    response = dashscope.Generation.call(
        model='qwen-plus',
        prompt=prompt
    )
    if response.status_code == 200:
        script_text = response.output.text
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, 'showrunner.private')
        with open(file_path, 'w') as f:
            f.write(script_text)
        return script_text
    else:
        return f"Error generating script: {response.message}"

def render_video(script: str, resolution: str = "1280x720", duration: int = 5, style: str = "font=Arial:fontsize=24:fontcolor=white") -> None:
    """Renders a video from the script using subtitles.

    Args:
        script: The script text to render.
        resolution: The resolution of the output video (e.g., "1280x720").
        duration: The duration in seconds for each line of the script.
        style: The subtitle style parameters for ffmpeg.

    Returns:
        None. The video is saved as 'output.mp4'.
    """
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
