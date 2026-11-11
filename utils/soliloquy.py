import random
import re
from utils.seven_bag import seven_bag
from utils import file_paths as paths

with paths.SENTENCES.open() as f:
    sentences = seven_bag([s for s in f.read().splitlines() if s])
with paths.NOUNS.open() as f:
    nouns = seven_bag(f.read().splitlines())

# replaces [noun] with random noun
def fill_sentence(sentence: str):
    return re.sub(r'\[noun\]', lambda m: nouns.get_item(), sentence)

def construct_abomination(n: int):
    abomination = ''
    for _ in range(n):
        abomination += fill_sentence(sentences.get_item()) + ' '
    return abomination.strip()
