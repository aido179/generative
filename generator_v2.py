import time, random
from collections import deque
from typing import List, Callable, Any, Tuple
from colored import fg, bg, attr

"""
V2 - instead of each boxel determining the output, a cursor moves around the canvas and draws the picture.
Boxels determine where the cursor goes next
(originally, the boxel determined what colour was drawn, but it wasn't very pleasing. Now the cursor just brightens a pixel)
"""

greys = ["grey_3", "grey_7","grey_11","grey_15","grey_19","grey_23","grey_27","grey_30","grey_35","grey_39","grey_42","grey_46","grey_50","grey_54","grey_58","grey_62","grey_66","grey_70","grey_74","grey_78","grey_82","grey_85","grey_89", "grey_93"]

class Boxel:
    def __init__(self, color_val_range=255):
        self.cursor_next_position:Tuple[int,int] = (0,0)
        self.set_cursor_next_position()
        self.cursor_next_color = random.randrange(color_val_range)

        self.max_energy = 99
        self.energy = 99
        self.cost = 50
        self.regeneration_rate = 1

        self.last_step_visited = 0

    def set_cursor_next_position(self) -> None:
        positions = [
            (0, -1), # north
            (-1, -1),# nw
            (-1, 0), # west
            #(-1, 1), # sw
            #(0, 1), # south
            #(1, 1), # se
            (1, 0), # east
            (1, -1) # ne
        ]
        index = random.randrange(len(positions))
        self.cursor_next_position = positions[index]

    def isDead(self):
        return self.energy <= 0

    def energize(self):
        if not self.isDead() and self.energy < self.max_energy:
            self.energy+=self.regeneration_rate

    def deenergize(self):
        if self.energy > 0:
            self.energy -= self.cost

    def visit(self, curr_step:int) -> None:
        # calculate the energy that accumulated over the steps since last visited.
        steps_since_last_visit = curr_step - self.last_step_visited
        potential_energy = self.energy + (self.regeneration_rate * steps_since_last_visit)
        self.energy = min(self.max_energy, self.energy)
        # de-energize for this step
        self.deenergize()


class Cursor:
    def __init__(self, h:int, w:int):
        self.size = (h, w)
        self.pos = (random.randrange(w), random.randrange(h))
        self.col = random.randrange(MAX_VAL)

        self.lifespan = 50000
        self.curr_age = 0
        self.aging_rate = 1000

    def age(self, step:int) -> None:
        self.curr_age += self.aging_rate
        if self.curr_age >= self.lifespan:
            self.pos = (random.randrange(self.size[1]), random.randrange(self.size[0]))
            self.col = random.randrange(MAX_VAL)
            self.curr_age = 0
            self.aging_rate -= max(1, self.aging_rate -1)

# types
BoxelArray = List[List[Boxel]]
StateArray = List[List[int]]

def clear_screen() -> str:
    return '\033[2J'

def move_cursor(x:int,y:int)-> str:
    return ("\033[%d;%dH" % (x, y))

def print_state_colors(state:StateArray) -> None:
    out = ""
    #out = clear_screen()
    out += move_cursor(0,0)
    for row in state:
        for col in row:
            out += fg(greys[col])+"██"
        out+="\n"
    print(out, attr('reset'))

def print_boxel_energy(boxels:BoxelArray) -> None:
    out = ""
    #out = clear_screen()
    out += move_cursor(CANVAS_H,0)
    for row in boxels:
        for bxl in row:
            #out += fg(greys[bxl.energy*4])+"██"
            out += f"{bxl.energy} "
        out+="\n"
    print(out, attr('reset'))


def updateState(state:StateArray, cursor: Cursor) -> StateArray:
    (x, y) = cursor.pos
    state[y][x] = min(MAX_VAL, state[y][x]+1) #cursor.col
    return state

def updateCursor(step:int, boxels:BoxelArray, cursor:Cursor) -> Cursor:
    (x, y) = cursor.pos
    b = boxels[y][x]
    #cursor.pos = tuple(map(sum, zip(cursor.pos, b.cursor_next_position)))
    new_x = (cursor.pos[0] + b.cursor_next_position[0]) % cursor.size[0]
    new_y = (cursor.pos[1] + b.cursor_next_position[1]) % cursor.size[1]
    cursor.pos = (new_x, new_y)
    cursor.col = (cursor.col + b.cursor_next_color) % MAX_VAL
    cursor.age(step)
    return cursor

def updateBoxels(step:int, boxels:BoxelArray, cursor:Cursor) -> BoxelArray:
    cx, cy = cursor.pos
    boxels[cy][cx].visit(step)
    if boxels[cy][cx].isDead():
        boxels[cy][cx] = Boxel()
    # for x, row in enumerate(boxels):
    #     for y, b in enumerate(row):
    #         b.energize()
    #         if b.isDead():
    #             boxels[x][y] = Boxel()
    return boxels

def initBoxels(h:int, w:int, boxel_generator:Callable[[], Boxel]) -> BoxelArray:
    out:BoxelArray = []
    for x in range(0, h):
        out.append([])
        for y in range(0, w):
            out[x].append(boxel_generator())
    return out

def initState(h:int, w:int, val_generator:Callable[[], int]) -> StateArray:
    out:StateArray = []
    for x in range(0, h):
        out.append([])
        for y in range(0, w):
            out[x].append(val_generator())
    return out

def boxelGenerator() -> Boxel:
    return Boxel(color_val_range=MAX_VAL)

def stateGenerator() -> int:
    return 0


MAX_VAL = 23 # 23 because there are 23 grey colours to display
CANVAS_H, CANVAS_W = 100, 100
def main():
    #h, w = 79, 79

    boxels = initBoxels(CANVAS_H, CANVAS_W, boxelGenerator)
    state = initState(CANVAS_H, CANVAS_W, stateGenerator)
    cursor = Cursor(CANVAS_H, CANVAS_W)
    print_state_colors(state)
    #print_boxel_energy(boxels)
    step = 0
    while True:
        state = updateState(state, cursor)
        cursor = updateCursor(step, boxels, cursor)
        boxels = updateBoxels(step, boxels, cursor)
        if step % 500 == 0:
            print_state_colors(state)
            #print_boxel_energy(boxels)
            print(cursor.curr_age)
        step+=1
        #time.sleep(0.01)

main()
