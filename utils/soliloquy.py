import random
import re
from utils.seven_bag import seven_bag
from utils import file_paths as paths

sentences = seven_bag([s for s in paths.SENTENCES.read_text().splitlines() if s])
nouns = seven_bag(paths.NOUNS.read_text().splitlines())

# replaces [noun] with random noun
def fill_sentence(sentence: str):
    return re.sub(r'\[noun\]', lambda m: nouns.get_item(), sentence)

def construct_abomination(n: int):
    abomination = ''
    for _ in range(n):
        abomination += fill_sentence(sentences.get_item()) + ' '
    return abomination.strip()
