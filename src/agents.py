import random, math, traceback, sys
import numpy as np
import cv2
from src import tools
from src import brushes
from typing import Callable, List, Tuple, Any

class Agent:
    def __init__(self) -> None:
        self.position = (0,0)
        self.next_position = (0,0)
        self.position_history: List[Tuple[int, int]] = [self.position]
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
        self.lifespan = 50000
        self.curr_age = 0
        self.aging_rate = 500
        self.brush:Callable[[np.ndarray, List[Tuple[int, int]]], np.ndarray] = brushes.simpleBorderPolyLine

    def calculateNextPosition(self):
        return self.position

    def checkDead(self, state:np.ndarray) -> bool:
        return False

    def doSpawn(self) -> None:
        pass

    def doDraw(self, state:np.ndarray) -> None:
        state = self.brush(state, self.position_history)

    def doStep(self, step:int, state:np.ndarray, terrain:np.ndarray) -> np.ndarray:
        # 1. Calculate new position
        self.new_point = self.calculateNextPosition()
        # 2. Check if dead
        if self.checkDead(state):
            return state
        # 3. Do spawn
        self.doSpawn()
        # 4. Do draw
        self.doDraw(state)
        # 5. Do step
        self.position = self.next_position
        self.position_history.append(self.next_position)
        self.curr_age += self.aging_rate
        #self.curr_age += self.aging_rate
        self.direction_rads = terrain[self.position[0]][self.position[1]]
        return state

    def die(self, x:Any=0) -> None:
        self.dead = True
        #print(x)

    def polarToCartesian(self, vector:Tuple[float, float]) -> Tuple[int, int]:
        """
        vector is a (distance, direction) tuple. aka (r, θ)
        returns a cartesian (x, y) point rounded to nearest integer.
        """
        x = vector[0] * math.cos(vector[1])
        y = vector[0] * math.sin(vector[1])
        return (int(round(x)), int(round(y)))

    def addPoints(self, p1:Tuple[int, int], p2:Tuple[int, int]) -> Tuple[int, int]:
        return (p1[0]+p2[0], p1[1]+p2[1])

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



    def step(self, step:int, state:np.ndarray, original_image:np.ndarray) -> np.ndarray:
        # Calculate step
        cartesian_step = self.polarToCartesian((self.step_distance, math.radians(self.step_direction)))
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

    def spawn(self, state: np.ndarray) -> None:
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

def getFrostDrawerAroundRandomSeedPoint(CANVAS_H:int, CANVAS_W:int, angle_beween:int, agent_buffer:List[Agent]) -> None:
    offset_angle = int(angle_beween * random.random())
    point = (random.randrange(CANVAS_H), random.randrange(CANVAS_W))
    # point = (300, 150)
    # print(CANVAS_H, CANVAS_W)
    for theta in range(0,360,angle_beween):
        c = FrostDrawer(agent_buffer, (CANVAS_H, CANVAS_W))
        c.pos = point
        c.step_direction = theta+offset_angle
        agent_buffer.append(c)

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

    def doStep(self, step:int, state:np.ndarray, terrain:np.ndarray) -> np.ndarray:
        # 1. Calculate new position
        """ Never change position, but calculate draw here """
        end_point_diff = self.polarToCartesian((self.magnitude, self.direction_rads))
        end_point = self.addPoints(self.position, end_point_diff)
        # 2. Check if dead
        """ Die immediately """
        self.die()
        # 3. Do spawn
        """ Never spawn """
        # 4. Do draw
        # draw a line indicating the vector field value at this position.
        # ie, draw a line at the vector angle and with a length representing the magnitude.
        state = cv2.line(state,self.position[::-1],end_point[::-1],self.color,self.stroke_width)
        # 5. Do step
        """ never change on step """
        return state

def VectorFieldVisualizerFactory(vectorField:np.ndarray, agent_buffer:List[Agent], granularity:int) -> List[Agent]:
    shape = vectorField.shape
    for x in range(0, shape[0], granularity):
        for y in range(0, shape[1], granularity):
            v = VectorFieldVisualizer(agent_buffer, (x, y), granularity/2, vectorField[x][y])
            agent_buffer.append(v)
    return agent_buffer

class VectorFieldWalker(Agent):
    """
    An agent that follows the vector direction
    """
    def __init__(self, cursor_list:List[Agent], position:Tuple[int, int], magnitude:float=1, direction_rads:float=0):
        super().__init__()
        self.cursor_list = cursor_list
        self.position = position
        self.next_position = position
        self.position_history: List[Tuple[int, int]] = [position]

        self.brush:Callable[[np.ndarray, List[Tuple[int, int]]], np.ndarray] = brushes.simpleBorderPolyLine

        self.magnitude=magnitude
        self.direction_rads=direction_rads

        self.dead = False

    def calculateNextPosition(self) -> Tuple[int,int]:
        new_point_diff = self.polarToCartesian((self.magnitude, self.direction_rads))
        new_point = self.addPoints(self.position, new_point_diff)
        return new_point

    def checkDead(self, state:np.ndarray) -> bool:
        # if too much points (probably in an infinite loop)
        if len(self.position_history) > 5000:
            self.die('too big')
            return True
        # if too old
        if self.curr_age > self.lifespan:
            self.die(1)
            return True
        # if outside the image
        # state.shape is in cv2 [w h] shape. position is in drawing [h w] shape
        # if self.next_position[0] < 0 or self.next_position[1] < 0 or self.next_position[0] >= state.shape[0] or self.next_position[1] >= state.shape[1]:
        #     self.die(2)
        #     return True
        return False

    def doDraw(self, state:np.ndarray) -> None:
        state = self.brush(state, self.position_history)

    def doStep(self, step:int, state:np.ndarray, terrain:np.ndarray) -> np.ndarray:
        # 1. Calculate new position
        self.next_position = self.calculateNextPosition()
        # 2. Check if dead
        if self.checkDead(state):
            return state
        # 3. Do spawn
        self.doSpawn()
        # 4. Do draw
        self.doDraw(state)
        # 5. Do step
        self.position = self.next_position
        self.position_history.append(self.next_position)
        self.curr_age += self.aging_rate
        try:
            self.direction_rads = terrain[self.position[0]][self.position[1]]
        except IndexError:
            pass
        return state

class VectorFieldBackwardWalker(VectorFieldWalker):
    """
    This is a version of VectorFieldWalker that moves backwards,
    or 180 offset from the terrain direction.

    It does no drawing, but the position_history is used by a corresponding
    "front facing" VectorFieldWalker to draw a full line in two directions
    """
    def __init__(self, cursor_list:List[Agent], position:Tuple[int, int], partner_walker:VectorFieldWalker, magnitude:float=1, direction_rads:float=0):
        super().__init__(cursor_list, position, magnitude, direction_rads)
        self.partner_walker = partner_walker

    def calculateNextPosition(self) -> Tuple[int,int]:
        new_point_diff = self.polarToCartesian((0-self.magnitude, self.direction_rads))
        new_point = self.addPoints(self.position, new_point_diff)
        # Inject my positin into the partner walker's position history
        self.partner_walker.position_history.insert(0, new_point)
        return new_point

    def doDraw(self, state):
        pass


def VectorFieldWalkerFactory_1(vectorField:np.ndarray, agent_buffer:List[Agent], count:int) -> List[Agent]:
    """
    Create 'count' walkers at random locations
    """
    shape = vectorField.shape
    for x in range(0, count):
        pos = (random.randrange(shape[0]), random.randrange(shape[1]))
        v = VectorFieldWalker(agent_buffer, pos, 10, vectorField[pos[0]][pos[1]])
        agent_buffer.append(v)
    return agent_buffer

def VectorFieldWalkerFactory_2(vectorField:np.ndarray, agent_buffer:List[Agent], step:int) -> List[Agent]:
    """
    Create walkers at regular locations all over the terrain at 'step' intervals
    """
    shape = vectorField.shape
    for x in range(0, shape[0], step):
        for y in range(0, shape[1], step):
            # build the brush function

            v = VectorFieldWalker(agent_buffer, (x, y), 2, vectorField[x][y])
            bsh = brushes.simpleBorderPolyLine
            v.brush = bsh
            agent_buffer.append(v)
    return agent_buffer

def VectorFieldWalkerFactory_3(vectorField:np.ndarray, agent_buffer:List[Agent], step:int) -> List[Agent]:
    """
    Create walkers on a vertical line throught the middle of the terrain
    """
    shape = vectorField.shape
    y = int(shape[1]/2)
    for x in range(0, shape[0], step):
        v = VectorFieldWalker(agent_buffer, (x, y), 10, vectorField[x][y])
        v_back = VectorFieldBackwardWalker(agent_buffer, (x, y), v, 10, vectorField[x][y])
        bsh = brushes.simpleBorderPolyLine
        v.brush = bsh
        agent_buffer.append(v)
        agent_buffer.append(v_back)
    return agent_buffer
