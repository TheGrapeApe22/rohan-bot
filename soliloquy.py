import json
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

    def get_item(self, item=None):
        if item is None:
            item = self.bag.pop()
        else:
            self.bag.remove(item)

        if len(self.bag) == 0:
            self.refill_bag()
        return item


# init from file
with open('assets/memes.json') as f:
    source = json.load(f)

sentence_frames: seven_bag = seven_bag(source['sentences'])
insertions = source['insertions']
for (placeholder, insertion) in insertions.items():
    insertions[placeholder] = seven_bag(insertion)

# replaces all placeholders with random insertions from the corresponding bag
def fill_sentence(sentence: str):
    for placeholder, insertion in insertions.items():
        sentence = re.sub(f'\\{placeholder}', lambda m: insertion.get_item(), sentence)
    return sentence

def get_random_sentence(tag):
    for sentence in sentence_frames.bag:
        if tag in sentence['tags']:
            return fill_sentence(sentence_frames.get_item(sentence)['sentence'])
    return None

def construct_abomination(tags=['beginning', 'middle', 'middle', 'middle', 'end']):
    abomination = ''
    for tag in tags:
        sentence = get_random_sentence(tag)
        if sentence is not None:
            abomination += sentence + ' '
    return abomination.strip()
