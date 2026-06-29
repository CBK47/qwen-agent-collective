from collections import deque
import datetime

class Brain:
    def __init__(self, token_budget: int):
        self.token_budget = token_budget
        self.facts = deque()
        self.total_tokens = 0

    def add_fact(self, fact_data, token_count):
        current_time = datetime.datetime.now()
        while self.total_tokens + token_count > self.token_budget and self.facts:
            oldest = self.facts.popleft()
            self.total_tokens -= oldest[1]
        self.facts.append((current_time, token_count, fact_data))
        self.total_tokens += token_count
