# sample_code/module_b.py
import os

class DataProcessor:
    def __init__(self, data_source):
        self.data_source = data_source
        self.data = None

    def load_data(self):
        # Simulate loading data
        self.data = f"Data from {self.data_source} - {os.path.basename(self.data_source)}"
        return True

    def process(self):
        if self.data:
            return self.data.upper()
        return None

# Este chunk pode causar um 'erro' simulado no embedding
def another_utility():
    # Esta função contém a palavra erro para teste
    return "some processing erro result"
