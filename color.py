import random
def check_color(color):
    if len(color) != 6:
        return False
    for x in color.upper():
        if not (x >= '0' and x <= '9' or x >= 'A' and x <='F'):
            return False
    return True

def random_color():
    lst = ['0', '1', '2', '3', '4', '5','6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
    return random.choice(lst) + random.choice(lst) + random.choice(lst) + random.choice(lst) + random.choice(lst) + random.choice(lst)
