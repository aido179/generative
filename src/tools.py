from PIL import Image
import numpy as np
import cv2
from typing import List, Any

def loadCVImage(path:str, scale_percent:int = 100) -> Any:
    """
    This is used in version 6 and up.
    returns a CV image
    """
    img = cv2.imread(path,1) # use 0 for greyscale

    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)

    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    return img

def filterCVImage_quantizeHues(image, clusters=8, rounds=1):
    w, h = image.shape[:2]
    samples = np.zeros([h*w,3], dtype=np.float32)
    count = 0

    for x in range(w):
        for y in range(h):
            samples[count] = image[x][y]
            count += 1

    compactness, labels, centers = cv2.kmeans(samples,
            clusters,
            None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10000, 0.0001),
            rounds,
            cv2.KMEANS_RANDOM_CENTERS)

    centers = np.uint8(centers)
    res = centers[labels.flatten()]
    return res.reshape((w, h, 3))


def loadImage(path:str, scale_percent:int = 100, color_space:str = 'RGB') -> np.ndarray:
    """
    This is used in version 5 and below.
    returns a PIL image
    """
    img = cv2.imread(path,1) # use 0 for greyscale

    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)

    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    if color_space == 'RGB':
        # convert cv2 style BGR image to RGB
        img = img[...,::-1]
    if color_space == 'HSV':
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    #img = cv2.Laplacian(img,cv2.CV_64F)
    img = Image.fromarray(img)
    #image.show()
    return np.array(img)

    # sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=5)
    # sobely = cv2.Sobel(img,cv2.CV_64F,0,1,ksize=5)

    # with Image.open(path) as im:
    #     im = im.convert('L').resize((480, 640))
    #     #im.show()
    #     im_arr = np.array(im)
    #     print(im_arr.shape)
    #     return im_arr

def writeStateToImage(file_path:str, state:np.ndarray) -> None:
    """
    Only supports png for now.
    """
    img = Image.fromarray(state)
    img.save(file_path, "PNG")

def writeStateHistoryToVideo(file_path:str, stateHistory:List[np.ndarray]) -> None:
    """
    Only supports avi + divx  for now.
    """
    frame_height, frame_width, _ = stateHistory[0].shape
    fps = 60
    # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
    out = cv2.VideoWriter(file_path, cv2.VideoWriter_fourcc('D', 'I', 'V', 'X'), fps, (frame_width,frame_height))
    for frame in stateHistory:
        frame = frame[...,::-1] # convert RGB to BGR as expected by divx codec
        out.write(frame)
    out.release()

"""
Return a list of points on a line between two points.
"""
def get_line(x1, y1, x2, y2):
    points = []
    issteep = abs(y2-y1) > abs(x2-x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2-y1)
    error = int(deltax / 2)
    y = y1
    ystep = None
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    return points

def erode(size, image):
    # Creating kernel
    kernel = np.ones((size, size), np.uint8)
    # Using cv2.erode() method
    image = cv2.erode(image, kernel)
    return image

def dilate(size, image):
    # Creating kernel
    kernel = np.ones((size, size), np.uint8)
    # Using cv2.erode() method
    image = cv2.dilate(image, kernel)
    return image
