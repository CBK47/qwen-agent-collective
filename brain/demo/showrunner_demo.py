import argparse
from showrunner.agent import ShowrunnerAgent
import pyautogui
import cv2
import numpy as np
import threading

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_events', type=int, required=True)
    args = parser.parse_args()

    agent = ShowrunnerAgent()
    print("Initializing Showrunner Agent...")
    script_content = agent.generate_script(num_events=args.num_events)
    with open('showrunner.private', 'w') as f:
        f.write(script_content)
    print("Script generated and saved to showrunner.private")

    agent.load_script(script_content)
    print("Generating video...")

    recording = True
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('demo_recording.avi', fourcc, 20.0, screen_size)

    def record_screen():
        while recording:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            out.write(frame)
        out.release()

    recording_thread = threading.Thread(target=record_screen)
    recording_thread.start()

    video_path = agent.generate_video(output_dir="demo_output")

    recording = False
    recording_thread.join()

    print(f"Demo video generated at {video_path}")

if __name__ == "__main__":
    main()
