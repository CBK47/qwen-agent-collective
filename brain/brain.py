from collections import deque
import datetime

class Brain:
    def __init__(self, token_budget: int):
        """
        Initializes the Brain instance with a token budget.

        Args:
            token_budget (int): The maximum number of tokens allowed for stored facts.
        """
        self.token_budget = token_budget
        self.facts = deque()
        self.total_tokens = 0

    def add_fact(self, fact_data, token_count):
        """
        Adds a fact to the brain's memory, evicting the oldest facts if the token budget is exceeded.

        Args:
            fact_data: The data of the fact to store.
            token_count (int): The number of tokens consumed by this fact.
        """
        current_time = datetime.datetime.now()
        while self.total_tokens + token_count > self.token_budget and self.facts:
            oldest = self.facts.popleft()
            self.total_tokens -= oldest[1]
        self.facts.append((current_time, token_count, fact_data))
        self.total_tokens += token_count
