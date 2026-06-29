from showrunner.agent import ShowrunnerAgent

def main():
    agent = ShowrunnerAgent()
    print("Initializing Showrunner Agent...")
    sample_script = """
    Scene 1: A sunny park. Alice walks towards a bench.
    Scene 2: Alice sits on the bench and reads a book.
    """
    agent.load_script(sample_script)
    print("Generating video...")
    video_path = agent.generate_video(output_dir="demo_output")
    print(f"Demo video generated at {video_path}")

if __name__ == "__main__":
    main()
