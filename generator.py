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
from src import agents

"""
V7 - flow paths

"""

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


def updateState(step:int, state:StateArray, terrain:StateArray, agent_buffer: List[agents.Agent]) -> StateArray:
    #print(len(agent_buffer))
    if len(agent_buffer) < 10:
        #agent_buffer.append(Cursor(agent_buffer, (state.shape[1], state.shape[0]))) # must reverse cv2 shape
        #getCrystalAgentsAroundRandomSeedPoint(state.shape[0], state.shape[1], 60, agent_buffer)
        agent_buffer = agents.VectorFieldWalkerFactory(terrain, agent_buffer, 1)
        pass
    for agent in agent_buffer:
        state = agent.doStep(step, state, terrain)
        if agent.dead:
            agent_buffer.remove(agent)
    return state

def updateStateHistory(step:int, every:int, state:StateArray, state_history:List[StateArray]) -> List[StateArray]:
    if step % every == 0:
        state_history.append(state.copy())
    return state_history

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

    noise_arr = noise.generate_perlin_noise_2d((480, 640), (10, 10), tileable=(False, False))
    terrain = noise_arr.copy() # keep terrain in 2d format.
    terrain = ((terrain + 1) * 6) # range 0-255
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
    agent_buffer:List[agents.Agent] = []
    #agents.VectorFieldVisualizerFactory(terrain, agent_buffer, 30)
    agents.VectorFieldWalkerFactory(terrain, agent_buffer, 10)
    print(f"agents: {len(agent_buffer)}")



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
            state = updateState(step, state, terrain, agent_buffer)

            state_history = updateStateHistory(step, steps_per_frame, state, state_history)
            if step % steps_per_frame == 0:
                draw(screen, state)
            # if step % 10000 == 0:
            #     print()
            #     for c in agent_buffer:
            #         c.print()
                #print_boxel_energy(boxels)
                #print(cursor.curr_age)
            step+=1
            #time.sleep(0.01)
        if not outer_loop:
            break
        erode_loop = False
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
