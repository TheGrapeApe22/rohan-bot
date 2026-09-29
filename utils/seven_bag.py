# 7bag from tetris
import random


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