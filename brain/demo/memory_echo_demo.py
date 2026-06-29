import time
from brain.agents.memory_echo import MemoryEchoAgent

def main():
    agent = MemoryEchoAgent()
    sample_inputs = [
        "Hello, how are you?",
        "What's the weather like today?",
        "Tell me a joke."
    ]
    for query in sample_inputs:
        print(f"User: {query}")
        response = agent.process(query)
        print(f"Agent: {response}")
        print("\n" + "-"*50 + "\n")
        time.sleep(2)

if __name__ == "__main__":
    main()
