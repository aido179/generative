import cv2
import numpy as np
from typing import Tuple, List

"""
Functions that draw brush strokes.

Underscore functions require all args to be provided. These are "raw brushes".

Functions without underscores (eg: simpleRedLine) should wrap a raw brush with specific args.
The only args should be the "state", the start position and end position.
"""

def _line(state:np.ndarray, start:Tuple[int, int], end:Tuple[int, int], color:List[int], stroke_width:int) -> np.ndarray:
     state = cv2.line(state, start, end, color, stroke_width)
     return state

def simpleRedLine(state:np.ndarray, start:Tuple[int, int], end:Tuple[int, int]) -> np.ndarray:
    return _line(state, start, end, [255, 0, 0], 1)

def _borderPolyLine(state:np.ndarray, points:List[Tuple[int, int]], line_color:List[int], border_color:List[int], stroke_width:int, border_thickness:int) -> np.ndarray:
    pts = np.array(list(map(lambda x: x[::-1], points)), np.int32)
    pts = pts.reshape((-1,1,2))
    border_line = stroke_width + (border_thickness * 2)
    state = cv2.polylines(state,[pts],False,border_color, thickness = border_line)
    state = cv2.polylines(state,[pts],False,line_color, thickness = stroke_width)
    return state


def simpleBorderPolyLine(state:np.ndarray, points:List[Tuple[int, int]]) -> np.ndarray:
    return _borderPolyLine(state, points, [255,255,255], [0,0,0], 10, 2)
