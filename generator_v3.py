import pygame
from pygame.locals import *
import numpy as np
import time, random, sys
from collections import deque
from typing import List, Callable, Any, Tuple
from colored import fg, bg, attr

"""
V3 - instead of each boxel determining the output, a cursor moves around the canvas and draws the picture.
Boxels determine where the cursor goes next.
Use pygame as live output.
Optimize boxel updating.
"""

greys = ["grey_3", "grey_7","grey_11","grey_15","grey_19","grey_23","grey_27","grey_30","grey_35","grey_39","grey_42","grey_46","grey_50","grey_54","grey_58","grey_62","grey_66","grey_70","grey_74","grey_78","grey_82","grey_85","grey_89", "grey_93"]

class Cursor:
    def __init__(self, h:int, w:int):
        self.size = (w, h)
        print(self.size)
        self.pos = (random.randrange(w), random.randrange(h))
        self.previous_pos = (self.pos[0]-1, self.pos[1]-1)
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

    def updatePosition(self, new_pos:Tuple[int, int]) -> None:
        self.previous_pos = self.pos
        self.pos = new_pos

class Boxel:
    def __init__(self, color_val_range=255):
        # self.cursor_next_position:Tuple[int,int] = (0,0)
        # self.set_cursor_next_position()
        self.cursor_movement_mode = self.mode1
        self.setCursorMovementMode()
        self.mode1_index:int = -1
        self.cursor_next_color = random.randrange(color_val_range)

        self.max_energy = 99
        self.energy = 99
        self.cost = 50
        self.regeneration_rate = 1

        self.last_step_visited = 0
    #
    # def set_cursor_next_position(self) -> None:
    #     positions = [
    #         (0, -1), # north
    #         (-1, -1),# nw
    #         (-1, 0), # west
    #         #(-1, 1), # sw
    #         #(0, 1), # south
    #         #(1, 1), # se
    #         (1, 0), # east
    #         (1, -1) # ne
    #     ]
    #     index = random.randrange(len(positions))
    #     self.cursor_next_position = positions[index]

    def setCursorMovementMode(self):
        modes = [
            self.mode1,
            self.mode2
        ]
        self.cursor_movement_mode = random.choice(modes)

    def getCursorNextPosition(self, cursor:Cursor) -> Tuple[int,int]:
        return self.cursor_movement_mode(cursor)

    def mode1(self, cursor:Cursor) -> Tuple[int,int]:
        positions = [
                (0, -1), # north
                (-1, -1),# nw
                (-1, 0), # west
                (-1, 1), # sw
                (0, 1), # south
                (1, 1), # se
                (1, 0), # east
                (1, -1) # ne
            ]
        if self.mode1_index == -1:
            self.mode1_index = random.randrange(len(positions))
        return positions[self.mode1_index]

    def mode2(self, cursor:Cursor) -> Tuple[int,int]:
        return (0,0)

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




# types
BoxelArray = List[List[Boxel]]
StateArray = Any

def clear_screen() -> str:
    return '\033[2J'

def move_cursor(x:int,y:int)-> str:
    return ("\033[%d;%dH" % (x, y))

def draw(screen:pygame.surface.Surface, state:StateArray) -> None:
    # out = ""
    # #out = clear_screen()
    # out += move_cursor(0,0)
    # for row in state:
    #     for col in row:
    #         out += fg(greys[col])+"██"
    #     out+="\n"
    # print(out, attr('reset'))
    surface = pygame.surfarray.make_surface(state)
    screen.blit(surface, (0, 0))
    pygame.display.update()

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
    (y, x) = cursor.pos
    new_val = min(MAX_VAL, state[y][x][0]+1)
    state[y][x] = [new_val, new_val, new_val] #cursor.col
    return state

def updateCursor(step:int, boxels:BoxelArray, cursor:Cursor) -> Cursor:
    (y, x) = cursor.pos
    b = boxels[y][x]
    new_pos = b.getCursorNextPosition(cursor)
    new_x = (cursor.pos[0] + new_pos[0]) % cursor.size[0]
    new_y = (cursor.pos[1] + new_pos[1]) % cursor.size[1]
    cursor.updatePosition((new_x, new_y))
    cursor.col = (cursor.col + b.cursor_next_color) % MAX_VAL
    cursor.age(step)
    return cursor

def updateBoxels(step:int, boxels:BoxelArray, cursor:Cursor) -> BoxelArray:
    cx, cy = cursor.pos
    boxels[cx][cy].visit(step)
    if boxels[cx][cy].isDead():
        boxels[cx][cy] = Boxel()
    return boxels

def initBoxels(h:int, w:int, boxel_generator:Callable[[], Boxel]) -> BoxelArray:
    out:BoxelArray = []
    for x in range(0, w):
        out.append([])
        for y in range(0, h):
            out[x].append(boxel_generator())
    print(f"boxles:{len(out)}, {len(out[-1])}")
    return out

def initState(h:int, w:int) -> StateArray:
    state = np.zeros((w, h, 3), dtype=int)
    print(f"state: {state.shape}")
    return state

def boxelGenerator() -> Boxel:
    return Boxel(color_val_range=MAX_VAL)


MAX_VAL = 255
CANVAS_H, CANVAS_W = 640, 480
def main():
    pygame.init()
    screen = pygame.display.set_mode((CANVAS_W, CANVAS_H))
    #h, w = 79, 79

    boxels = initBoxels(CANVAS_H, CANVAS_W, boxelGenerator)
    state = initState(CANVAS_H, CANVAS_W)
    cursor = Cursor(CANVAS_H, CANVAS_W)
    draw(screen, state)
    #print_boxel_energy(boxels)
    step = 0
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN):
                sys.exit()
        state = updateState(state, cursor)
        cursor = updateCursor(step, boxels, cursor)
        boxels = updateBoxels(step, boxels, cursor)
        if step % 500 == 0:
            draw(screen, state)
            #print_boxel_energy(boxels)
            #print(cursor.curr_age)
        step+=1
        #time.sleep(0.01)

main()
