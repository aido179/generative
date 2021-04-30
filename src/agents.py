import random, math, traceback, sys
import numpy as np
import cv2
from src import tools
from typing import List, Tuple

class Agent:
    def __init__(self):
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

    def doStep(self):
        pass 
    def die(self, x=0):
        self.dead = True
        #print(x)

class FrostDrawer(Agent):
    def __init__(self, cursor_list:List[Agent], size:Tuple[int, int], spawn_rate:float=0.9, step_distance:float=10, step_direction:float=140):
        self.cursor_list = cursor_list

        self.size = size
        h = self.size[0]
        w = self.size[1]
        self.pos = (random.randrange(h), random.randrange(w))
        self.previous_pos = (self.pos[0]-1, self.pos[1]-1)
        self.color = [255, 255, 255]
        self.stroke_width = 1

        self.spawn_rate=spawn_rate
        self.step_distance=step_distance
        self.step_direction=step_direction

        self.lifespan = 50000
        self.curr_age = 0
        self.aging_rate = 500

        self.dead = False
        # cull cursors that wont move.
        if self.step_distance < 1:
            self.die()

    def polarToCartesian(self, vector:Tuple[float, float]) -> Tuple[int, int]:
        """
        vector is a (distance, direction) tuple. aka (r, θ)
        returns a cartesian (x, y) point rounded to nearest integer.
        """
        x = vector[0] * math.cos(math.radians(vector[1]))
        y = vector[0] * math.sin(math.radians(vector[1]))
        return (int(round(x)), int(round(y)))

    def step(self, step:int, state:np.ndarray, original_image:np.ndarray) -> np.ndarray:
        # Calculate step
        cartesian_step = self.polarToCartesian((self.step_distance, self.step_direction))
        new_pos = (self.pos[0]+cartesian_step[0], self.pos[1]+cartesian_step[1])
        x, y = self.pos
        x_1, y_1 = new_pos
        # check if dead
        # if too old
        if self.curr_age > self.lifespan:
            self.die(1)
            return state
        # if outside the image
        # state.shape is in cv2 [w h] shape. position is in drawing [h w] shape
        if x_1 < 0 or y_1 < 0 or x_1 >= state.shape[0] or y_1 >= state.shape[1]:
            self.die(2)
            return state
        try:
            # # if color is different
            new_color = original_image[x_1][y_1]
            old_color = original_image[x][y]
            if not (new_color[0] == old_color[0] and new_color[1] == old_color[1] and new_color[2] == old_color[2]):
                self.die(3)
                return state
            # if meet an existing line
            line_points = tools.get_line(x_1, y_1, x, y)
            for p in line_points[1:]:
                p_x, p_y = p
                if p_x == self.pos[0] and p_y == self.pos[1]:
                    continue # skip the current position
                if state[p_x][p_y][0] == 255:
                    self.die(4)
                    return state
        except IndexError as E:
            print(E)
            traceback.print_exc(file=sys.stdout)
            self.die(5)
            return state
        # Do spawn
        if random.random() < self.spawn_rate:
            self.spawn(state)
        # Do step
        state = cv2.line(state,self.pos[::-1],new_pos[::-1],self.color,self.stroke_width)
        self.previous_pos = self.pos
        self.pos = new_pos
        self.curr_age += self.aging_rate
        return state

    def spawn(self, state):
        new_direction = self.step_direction + random.choice([30, -30])
        new_step_distance = self.step_distance*0.8
        if new_step_distance < 1:
            return
        new_spawn_rate = min(self.spawn_rate*0.8, 1.0)
        new_lifespan = int(self.lifespan * 0.9)

        child = FrostDrawer(self.cursor_list, self.size, spawn_rate=new_spawn_rate, step_distance=new_step_distance, step_direction=new_direction)
        child.lifespan = new_lifespan
        #child.color = [self.color[0]-1,self.color[1]-1,self.color[2]-1]
        child.pos = self.pos
        self.cursor_list.append(child)

class VectorFieldVisualizer(Agent):
    """
    An agent that just draws the vector they are located at and does not move or change otherwise.
    """
    def __init__(self, cursor_list:List[Agent], position:Tuple[int, int], magnitude:float=10, direction_rads:float=140):
        self.cursor_list = cursor_list
        self.position = position

        self.color = [255, 0, 0]
        self.stroke_width = 1

        self.magnitude=magnitude
        self.direction_rads=direction_rads

        self.dead = False

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

    # def die(self, x=0):
    #     self.dead = True
    #     print(x)
