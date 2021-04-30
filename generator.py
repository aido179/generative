import pygame
from pygame.locals import *
import numpy as np
from PIL import Image
import cv2
import datetime, time, random, sys, math, traceback
from collections import deque
from typing import List, Callable, Any, Tuple

from src import tools
from src import waiter as wait
from src import noise

"""
V7 - flow paths

"""


class Cursor:
    def __init__(self, cursor_list:List['Cursor'], size:Tuple[int, int], spawn_rate:float=0.9, step_distance:float=10, step_direction:float=140):
        self.cursor_list = cursor_list


        self.size = size
        h = self.size[0]
        w = self.size[1]
        self.pos = (random.randrange(h), random.randrange(w))
        self.previous_positions:List[Tuple[int, int]] = [(self.pos[0]-1, self.pos[1]-1)]
        self.color = [255, 0, 0]
        self.stroke_width = 3

        self.step_distance=step_distance
        self.step_direction=step_direction

        self.lifespan = 50000
        self.curr_age = 0
        self.aging_rate = 500

        self.dead = False
        # cull cursors that wont move.
        if self.step_distance < 1:
            self.die()

        self.neighbour_positions = [
                (0, -1), # north
                (-1, -1),# nw
                (-1, 0), # west
                (-1, 1), # sw
                (0, 1), # south
                (1, 1), # se
                (1, 0), # east
                (1, -1) # ne
            ]

    def getNeighbourTerrainValues(self, terrain):
        values = []
        for p in self.neighbour_positions:
            values.append(terrain[self.pos[0]+p[0]][self.pos[1]+p[1]])
        return values

    def find_nearest_index(self, array, value, prev_pos):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx

    def step(self, step:int, state:np.ndarray, terrain:np.ndarray) -> np.ndarray:

        # Calculate step
        prev_pos = self.previous_positions[-1]
        n_vals = self.getNeighbourTerrainValues(terrain)
        curr_val = terrain[self.pos[0]][self.pos[1]]
        idx = self.find_nearest_index(n_vals, curr_val, prev_pos)
        step_pos = self.neighbour_positions[idx]
        new_pos = (self.pos[0]+step_pos[0], self.pos[1]+step_pos[1])
        x, y = self.pos
        x_1, y_1 = new_pos

        # check if dead
        # if too old
        # if self.curr_age > self.lifespan:
        #     self.die(1)
        #     return state
        # if outside the image
        # state.shape is in cv2 [w h] shape. position is in drawing [h w] shape
        if x_1 < 0 or y_1 < 0 or x_1 >= state.shape[0] or y_1 >= state.shape[1]:
            self.die(2)
            return state
        # # if color is different
        # new_color = original_image[x_1][y_1]
        # old_color = original_image[x][y]
        # if not (new_color[0] == old_color[0] and new_color[1] == old_color[1] and new_color[2] == old_color[2]):
        #     self.die(3)
        #     return state
        # if meet an existing line
        if new_pos in self.previous_positions:
            self.die(4)
            return state

        # Do spawn
        # if random.random() < self.spawn_rate:
        #     self.spawn(state)
        # Do step
        state = cv2.line(state,self.pos[::-1],new_pos[::-1],self.color,self.stroke_width)
        self.previous_positions.append(self.pos)
        self.pos = new_pos
        self.curr_age += self.aging_rate
        return state

    def die(self, x=0):
        self.dead = True
        print(x)




# # types
StateArray = Any
ImageArray = Any

def draw(screen:pygame.surface.Surface, state:ImageArray) -> None:
    img = state.copy()
    # swap axes from cv2 [x][y] style to pygame [y][x] style
    img = np.swapaxes(img, 0, 1)
    # move BGR to RGB
    img = img[...,::-1]
    surface = pygame.surfarray.make_surface(img)
    screen.blit(surface, (0, 0))
    pygame.display.update()


def updateState(step:int, state:StateArray, original_image:StateArray, cursors: List[Cursor]) -> StateArray:
    #print(len(cursors))
    if len(cursors) == 0:
        #cursors.append(Cursor(cursors, (state.shape[1], state.shape[0]))) # must reverse cv2 shape
        getCrystalCursorsAroundRandomSeedPoint(state.shape[0], state.shape[1], 60, cursors)

    for cursor in cursors:
        state = cursor.step(step, state, original_image)
        if cursor.dead:
            cursors.remove(cursor)
    return state

def updateStateHistory(step:int, every:int, state:StateArray, state_history:List[StateArray]) -> List[StateArray]:
    if step % every == 0:
        state_history.append(state.copy())
    return state_history


def getCrystalCursorsAroundRandomSeedPoint(CANVAS_H, CANVAS_W, angle_beween, cursors):
    offset_angle = int(angle_beween * random.random())
    point = (random.randrange(CANVAS_H), random.randrange(CANVAS_W))
    # point = (300, 150)
    # print(CANVAS_H, CANVAS_W)
    for theta in range(0,360,angle_beween):
        c = Cursor(cursors, (CANVAS_H, CANVAS_W))
        c.pos = point
        c.step_direction = theta+offset_angle
        cursors.append(c)

def handleEvents(pygame:Any) -> Tuple[bool, bool]:
    """
    Handles key presses to quit the program
    Returns updated loop control values
    """
    continue_outer_loop = True
    continue_current_loop = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == 113: #q
                continue_outer_loop = False
                continue_current_loop = False # gotta leave the inner loop before we can leave the outer one.
            if event.key == 13: #Enter
                continue_current_loop = False
    return (continue_outer_loop, continue_current_loop)


MAX_VAL = 255

# CANVAS_H, CANVAS_W = 720, 1280 # overwritten when an image is loaded
def main():
    print("Loading...")
    """
    Config
    openCV uses (W,H) .. (H,W) am I losing my mind?
    pygame uses (H,W)
    In this script use: (H,W) for drawing
    """
    steps_per_frame = 1
    image_scale_percent = 15

    noise_arr = noise.generate_perlin_noise_2d((480, 640), (4, 4), tileable=(False, False))
    terrain = noise_arr.copy() # keep terrain in 2d format.
    terrain = ((terrain + 1) * 128).astype(np.uint8) # range 0-255
    noise_arr = np.stack((noise_arr,)*3, axis=-1) # convert from 2d to 3d
    noise_arr = (noise_arr + 1) * 128 # range 0-255
    state = noise_arr.copy()



    original_image = state.copy()
    CANVAS_H, CANVAS_W, _ = state.shape
    pygame.init()
    pygame.font.init()
    myfont = pygame.font.SysFont('arial', 16)
    screen = pygame.display.set_mode((CANVAS_W, CANVAS_H))
    print("Loading complete.")
    #h, w = 79, 79

    #boxels = initBoxelsRandom(CANVAS_H, CANVAS_W)
    state_history = [state]
    cursors:List[Cursor] = []

    cursors.append(Cursor(cursors, (CANVAS_H, CANVAS_W)))
    cursors.append(Cursor(cursors, (CANVAS_H, CANVAS_W)))
    cursors.append(Cursor(cursors, (CANVAS_H, CANVAS_W)))
    cursors.append(Cursor(cursors, (CANVAS_H, CANVAS_W)))
    cursors.append(Cursor(cursors, (CANVAS_H, CANVAS_W)))

    draw(screen, state)
    #print_boxel_energy(boxels)

    step = 0
    outer_loop = True
    print("Outer loop")
    while outer_loop:
        draw_loop = True
        print("Draw loop")
        while draw_loop:
            outer_loop, draw_loop = handleEvents(pygame)
            state = updateState(step, state, terrain, cursors)

            state_history = updateStateHistory(step, steps_per_frame, state, state_history)
            if step % steps_per_frame == 0:
                draw(screen, state)
            # if step % 10000 == 0:
            #     print()
            #     for c in cursors:
            #         c.print()
                #print_boxel_energy(boxels)
                #print(cursor.curr_age)
            step+=1
            #time.sleep(0.01)
        if not outer_loop:
            break
        erode_loop = True
        print("Erode loop")
        waiter = wait.Waiter(0.1)
        while erode_loop:
            outer_loop, erode_loop = handleEvents(pygame)
            if waiter.checkDone():
                state = cv2.blur(state,(5,5))
                state = tools.erode(2, state)
                state_history = updateStateHistory(step, steps_per_frame, state, state_history)
                draw(screen, state)
                step+=1
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
    print("Save loop")
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
