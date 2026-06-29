import argparse
from showrunner.agent import ShowrunnerAgent

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
    video_path = agent.generate_video(output_dir="demo_output")
    print(f"Demo video generated at {video_path}")

if __name__ == "__main__":
    main()
