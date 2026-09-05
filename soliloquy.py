import random
import re

# 7bag from tetris
class seven_bag:
    def __init__(self, items):
        self.items = items
        self.bag = []
        self.refill_bag()

    def refill_bag(self):
        self.bag = self.items.copy()
        random.shuffle(self.bag)

    def get_item(self):
        if len(self.bag) == 0:
            self.refill_bag()
        return self.bag.pop()

with open('assets/sentences.txt') as f:
    sentences = seven_bag([s for s in f.read().splitlines() if s])
with open('assets/nouns.txt') as f:
    nouns = seven_bag(f.read().splitlines())

# replaces [noun] with random noun
def fill_sentence(sentence: str):
    return re.sub(r'\[noun\]', lambda m: nouns.get_item(), sentence)

def construct_abomination(n: int):
    abomination = ''
    for _ in range(n):
        abomination += fill_sentence(sentences.get_item()) + ' '
    return abomination.strip()
