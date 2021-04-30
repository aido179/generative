import pygame
from pygame.locals import *
import numpy as np
from PIL import Image
import datetime, time, random, sys
from collections import deque
from typing import List, Callable, Any, Tuple
from colored import fg, bg, attr

from src import tools

"""
V5
Save to video and image.
Cursors walk / draw image based on boxel direction.
boxel direction based on pixel neighbour colour similarity.
"""

greys = ["grey_3", "grey_7","grey_11","grey_15","grey_19","grey_23","grey_27","grey_30","grey_35","grey_39","grey_42","grey_46","grey_50","grey_54","grey_58","grey_62","grey_66","grey_70","grey_74","grey_78","grey_82","grey_85","grey_89", "grey_93"]

class Cursor:
    def __init__(self, h:int, w:int):
        self.size = (w, h)
        self.pos = (random.randrange(w), random.randrange(h))
        self.previous_pos = (self.pos[0]-1, self.pos[1]-1)
        self.color = [255, 255, 255]#MAX_VAL#random.randrange(MAX_VAL)

        self.lifespan = 50000
        self.curr_age = random.randrange(25000)
        self.aging_rate = 1000

    def age(self, step:int, boxel:'Boxel') -> None:
        self.curr_age += self.aging_rate
        #self.color = boxel.color
        if self.curr_age >= self.lifespan:
            self.pos = (random.randrange(self.size[0]), random.randrange(self.size[1]))
            self.color = boxel.color
            self.curr_age = 0
            #self.aging_rate = max(1, int(self.aging_rate*0.99))

    def updatePosition(self, new_pos:Tuple[int, int]) -> None:
        self.previous_pos = self.pos
        self.pos = new_pos

    def print(self) -> None:
        print(f"Cursor: Age:{self.curr_age}\tpos: {self.pos}\tage_rate:{self.aging_rate}")

class Boxel:
    def __init__(self, color_val_range=255, mode=-1):
        self.color = [255,255,255]
        # self.cursor_next_position:Tuple[int,int] = (0,0)
        # self.set_cursor_next_position()
        self.cursor_movement_mode = self.mode1
        self.setCursorMovementMode(mode)
        self.mode0_index:int = -1
        self.mode1_position = (0,0)
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

    def setCursorMovementMode(self, mode = -1):
        modes = [
            self.mode0,
            self.mode1
        ]
        if mode == -1:
            self.cursor_movement_mode = random.choice(modes)
        else:
            self.cursor_movement_mode = modes[mode]

    def getCursorNextPosition(self, cursor:Cursor) -> Tuple[int,int]:
        return self.cursor_movement_mode(cursor)

    def mode0(self, cursor:Cursor) -> Tuple[int,int]:
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
        if self.mode0_index == -1:
            self.mode0_index = random.randrange(len(positions))
        return positions[self.mode0_index]

    def mode1(self, cursor:Cursor) -> Tuple[int,int]:
        return self.mode1_position

    def setMode1Position(self, x:int, y:int, img_arr:Any) -> None:
        best_match_d_x = 0
        best_match_d_y = 0
        best_match = 500
        # avg similarity
        # my_val = sum(img_arr[x][y])/len(img_arr[x][y])
        # hue similarity (ensure load_image uses 'HSV' color_space)
        my_val = img_arr[x][y][0]
        for d_y in range(-1, 2):
            for d_x in range(-1, 2):
                # d_y and d_x are the relative coords of neighbouring pixels
                if d_x == 0 and d_y == 0: # skip the center point
                    continue
                # abs_y and abs_x are the absolute coords of neighbouring pixels
                abs_y = y+d_y
                abs_x = x+d_x
                if abs_y < 0 or abs_x < 0 or abs_y >= len(img_arr) or abs_x >= len(img_arr[0]): # skip edges
                    continue
                # avg similarity
                # new_val = sum(img_arr[abs_y][abs_x])/len(img_arr[abs_y][abs_x])
                # hue similarity
                new_val = img_arr[abs_y][abs_x][0]
                curr_sim = abs(my_val - new_val)
                if curr_sim < best_match:
                    best_match = curr_sim
                    best_match_d_x = d_x
                    best_match_d_y = d_y
        self.mode1_position = (best_match_d_y, best_match_d_x)

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
ImageArray = Any

def clear_screen() -> str:
    return '\033[2J'

def move_cursor(x:int,y:int)-> str:
    return ("\033[%d;%dH" % (x, y))

def draw(screen:pygame.surface.Surface, state:StateArray) -> None:
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


def updateState(step:int, state:StateArray, cursors: List[Cursor]) -> StateArray:
    # fade
    # if step % 500 == 0 :
    #     state[state>0] -= 1
    # draw
    for cursor in cursors:
        (x, y) = cursor.pos
        new_val = cursor.color
        # if new_val + state[x, y, 0] < 255:
        #     state[x, y] += new_val# [new_val, new_val, new_val]
        # else:
        #     state[x, y] = [255, 255, 255]
        state[x, y] = cursor.color
    return state

def updateStateHistory(step:int, state:StateArray, state_history:List[StateArray]) -> List[StateArray]:
    if step % 200 == 0:
        state_history.append(state.copy())
    return state_history


def updateCursors(step:int, boxels:BoxelArray, cursors:List[Cursor]) -> List[Cursor]:
    for cursor in cursors:
        try:
            x, y = cursor.pos
            b = boxels[y][x]
            new_pos = b.getCursorNextPosition(cursor)
            new_x = (cursor.pos[0] + new_pos[0]) % cursor.size[0]
            new_y = (cursor.pos[1] + new_pos[1]) % cursor.size[1]
            cursor.updatePosition((new_x, new_y))
            #cursor.color = (cursor.color + b.cursor_next_color) % MAX_VAL
            cursor.age(step, b)
        except IndexError as e:
            print(e)
            print(f"INDEX ERROR: boxels[{x}][{y}]")
            print(len(boxels))
            print(len(boxels[y]))
            pass
    return cursors

def updateBoxels(step:int, boxels:BoxelArray, cursors:List[Cursor]) -> BoxelArray:
    for cursor in cursors:
        x, y = cursor.pos
        try:
            boxels[y][x].visit(step)
            if boxels[y][x].isDead():
                retain_color = boxels[y][x].color
                boxels[y][x] = Boxel()
                boxels[y][x].color = retain_color
        except IndexError as e:
            print(e)
            print(f"INDEX ERROR: boxels[{y}][{x}]")
            print(len(boxels))
            #print(len(boxels[y]))
            pass
    return boxels

def initBoxelsRandom(h:int, w:int) -> BoxelArray:
    out:BoxelArray = []
    for x in range(0, h):
        out.append([])
        for y in range(0, w):
            out[x].append(Boxel(color_val_range=MAX_VAL))
    print(f"boxels:{len(out)}, {len(out[-1])}")
    return out

def initBoxelsFromImage(image:ImageArray)-> BoxelArray:
    out:BoxelArray = []
    for x in range(0, image.shape[0]):
        out.append([])
        for y in range(0, image.shape[1]):
            b = Boxel(color_val_range=MAX_VAL, mode=1)
            b.setMode1Position(x, y, image)
            b.color = image[x][y]
            out[x].append(b)
    return out


def initState(h:int, w:int) -> StateArray:
    state = np.zeros((w, h, 3), dtype=np.uint8)
    print(f"state: {state.shape}")
    return state

MAX_VAL = 255

CANVAS_H, CANVAS_W = 720, 1280 # overwritten when an image is loaded
def main():
    print("Loading...")
    """
    Config
    """
    image_scale_percent = 10
    image = tools.loadImage("img_in/G.jpeg", scale_percent=image_scale_percent)
    boxels = initBoxelsFromImage(image)
    CANVAS_H, CANVAS_W, _ = image.shape
    pygame.init()
    pygame.font.init()
    myfont = pygame.font.SysFont('arial', 16)
    screen = pygame.display.set_mode((CANVAS_W, CANVAS_H))
    print("Loading complete.")
    #h, w = 79, 79

    #boxels = initBoxelsRandom(CANVAS_H, CANVAS_W)
    state = initState(CANVAS_H, CANVAS_W)
    state_history = [state]
    cursors = [
        Cursor(CANVAS_H, CANVAS_W),
        Cursor(CANVAS_H, CANVAS_W),
        Cursor(CANVAS_H, CANVAS_W),
        Cursor(CANVAS_H, CANVAS_W),
        Cursor(CANVAS_H, CANVAS_W)
    ]
    draw(screen, state)
    #print_boxel_energy(boxels)
    step = 0
    draw_loop = True
    while draw_loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                draw_loop = False
        state = updateState(step, state, cursors)
        state_history = updateStateHistory(step, state, state_history)
        cursors = updateCursors(step, boxels, cursors)
        boxels = updateBoxels(step, boxels, cursors)
        if step % 500 == 0:
            draw(screen, state)
        # if step % 10000 == 0:
        #     print()
        #     for c in cursors:
        #         c.print()
            #print_boxel_energy(boxels)
            #print(cursor.curr_age)
        step+=1
        #time.sleep(0.01)
    #
    # Exit loop. Save image
    #
    timestamp = int(datetime.datetime.now().timestamp())
    output_image_path = f"output/time{timestamp}.png"
    output_video_path = f"output/time{timestamp}.avi"
    textsurface = myfont.render('Ended.', False, (255, 100, 0))
    screen.blit(textsurface,(0,0))
    textsurface = myfont.render('Press `s` to save image + video.', False, (255, 100, 0), (0,0,0))
    screen.blit(textsurface,(0,40))
    textsurface = myfont.render('Press any other key to quit.', False, (255, 100, 0), (0,0,0))
    screen.blit(textsurface,(0,80))
    textsurface = myfont.render(output_image_path, False, (255, 100, 0), (0,0,0))
    screen.blit(textsurface,(0,120))
    textsurface = myfont.render(output_video_path, False, (255, 100, 0), (0,0,0))
    screen.blit(textsurface,(0,160))
    pygame.display.update()
    save_loop = True
    while save_loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.unicode == 's':
                    tools.writeStateToImage(output_image_path, state)
                    tools.writeStateHistoryToVideo(output_video_path, state_history)
                save_loop = False
    return

main()
