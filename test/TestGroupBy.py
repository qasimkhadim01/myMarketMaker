from itertools import groupby


class Fruit:
    def __init__(self, name, count):
        self.name = name
        self.count = count

my_list = []
my_list.append(Fruit("apple", 5))
my_list.append(Fruit("banana", 6))
my_list.append(Fruit("orange", 6))
my_list.append(Fruit("banana", 9))
my_list.append(Fruit("orange", 3))
my_list.append(Fruit("apple", 111))

my_list2 = []
for i, g in groupby(sorted(my_list, key=lambda x: x.name)):
    my_list2.append([i.name, sum(v.count for v in g)])




print(my_list2)