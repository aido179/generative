import time, random
from collections import deque
from typing import List, Callable, Any
from colored import fg, bg, attr

"""
Prints an 'image' to console using box character and ansi colours.
Each 'boxel' (box pixel) is a function that determines it's output colour based on it's neighbours.
"""

greys = ["grey_3", "grey_7","grey_11","grey_15","grey_19","grey_23","grey_27","grey_30","grey_35","grey_39","grey_42","grey_46","grey_50","grey_54","grey_58","grey_62","grey_66","grey_70","grey_74","grey_78","grey_82","grey_85","grey_89", "grey_93"]
# types
BoxelOutput = Any
Boxel = Callable[['NeighbourArray'], BoxelOutput]
BoxelArray = List[List[Boxel]]
NeighbourArray = List[List[BoxelOutput]]
StateArray = List[List[BoxelOutput]]

# do nothing
def fn0(neighbours:NeighbourArray) -> BoxelOutput:
    return neighbours[1][1]

# move up
def fn1(neighbours:NeighbourArray) -> BoxelOutput:
    return neighbours[2][1]

# move down
def fn2(neighbours:NeighbourArray) -> BoxelOutput:
    return neighbours[0][1]

# move left
def fn3(neighbours:NeighbourArray) -> BoxelOutput:
    return neighbours[1][2]

# move right
def fn4(neighbours:NeighbourArray) -> BoxelOutput:
    return neighbours[1][0]

# pick avg
def fn5(neighbours:NeighbourArray) -> BoxelOutput:
    total = 0
    for x in neighbours:
        for val in x:
            total += val
    return int(total / 9)

# Random generator
def fn6(neighbours:NeighbourArray) -> BoxelOutput:
    return random.randrange(MAX_VAL)

def rotate(arr, n):
    d = deque(arr)
    d.rotate(n)
    return list(d)

def clear_screen() -> str:
    return '\033[2J'

def move_cursor(x:int,y:int)-> str:
    return ("\033[%d;%dH" % (x, y))

def print_state(state:StateArray) -> None:
    out = clear_screen()
    out += move_cursor(0,0)
    for row in state:
        for col in row:
            out += str(col)+" "
        out+="\n"
    print(out)

def int_grey(val:int) -> str:
    hex_string = hex(val)[2:]
    return f"#{hex_string}{hex_string}{hex_string}"

def print_state_colors(state:StateArray) -> None:
    out = ""
    #out = clear_screen()
    out += move_cursor(0,0)
    for row in state:
        for col in row:
            out += fg(greys[col])+"██"
        out+="\n"
    print(out, attr('reset'))

def getNeighbours(state:StateArray, x:int, y:int) -> NeighbourArray:
    neighbours = [
        [0,0,0],
        [0,0,0],
        [0,0,0]
    ]
    x_map = [-1, 0, 1]
    for (nx, x_dif) in enumerate(x_map):
        for (ny, y_dif) in enumerate(x_map):
            if (x+x_dif) > (len(state)-1): x-= len(state)
            if (y+y_dif) > (len(state)-1): y-= len(state)
            neighbours[nx][ny] = state[x+x_dif][y+y_dif]
    return neighbours


def updateState(step:int, state:StateArray, boxels:BoxelArray) -> StateArray:
    new_state = [
        [0,0,0],
        [0,0,0],
        [0,0,0]
    ]
    new_state = initState(len(state), len(state[0]), lambda: 0)
    for x in range(len(state)):
        for y in range(len(state)):
            n = getNeighbours(state,x,y)
            new_state[x][y] = boxels[x][y](n)
    return new_state

def initBoxels(h:int, w:int, val_generator:Callable[[], Boxel]) -> BoxelArray:
    out:BoxelArray = []
    for x in range(0, h):
        out.append([])
        for y in range(0, w):
            out[x].append(val_generator())
    return out

def initState(h:int, w:int, val_generator:Callable[[], BoxelOutput]) -> StateArray:
    out:StateArray = []
    for x in range(0, h):
        out.append([])
        for y in range(0, w):
            out[x].append(val_generator())
    return out

def boxelGenerator() -> Boxel:
    bxs = [fn0, fn1, fn2, fn3, fn4, fn5, fn6]
    wgt = [1, 4, 7, 10, 13, 14, 15]
    return random.choices(bxs, cum_weights=wgt, k=1)[0]

state_generator_counter = 0
def stateGenerator() -> BoxelOutput:
    #valid_states = "abcdefghijklmnopqrstuvwzyz0123456789"
    valid_states = list(range(0,MAX_VAL))
    global state_generator_counter
    val = valid_states[state_generator_counter]
    state_generator_counter += 1
    if state_generator_counter+1 > len(valid_states): state_generator_counter = 0
    return val


MAX_VAL = 23 # 23 because there are 23 grey colours to display
def main():
    h, w = 79, 79
    # boxels = [
    #     [fn1, fn1, fn1],
    #     [fn1, fn1, fn1],
    #     [fn1, fn1, fn1]
    # ]
    boxels = initBoxels(h, w, boxelGenerator)
    # state = [
    #     ['a', 'b', 'c'],
    #     ['d', 'e', 'f'],
    #     ['g', 'h', 'i']
    # ]
    state = initState(h, w, stateGenerator)
    print_state_colors(state)
    step = 0
    while True:
        new_state = updateState(step, state, boxels)
        #print_state(new_state)
        print_state_colors(new_state)
        state = new_state
        step+=1
        time.sleep(0.3)

main()
