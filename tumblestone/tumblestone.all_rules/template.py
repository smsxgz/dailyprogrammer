"""
Tumblestone Board Detector
Detects the game board state from a screenshot using computer vision
"""

import os
import cv2
import numpy as np
from PIL import ImageGrab
import win32gui
import time

def get_window_rect(window_title):
    """获取指定标题窗口的位置和大小"""
    window_handle = win32gui.FindWindow(None, window_title)
    if window_handle == 0:
        raise Exception(f'找不到窗口：{window_title}')
    
    win32gui.SetForegroundWindow(window_handle)
    time.sleep(0.1)
    
    client_rect = win32gui.GetClientRect(window_handle)
    pt1 = win32gui.ClientToScreen(window_handle, (0, 0))
    
    return (pt1[0], pt1[1], client_rect[2], client_rect[3])

def recognize_tile(tile, threshold=20):
    """识别tile的颜色"""
    # 计算tile的平均值，以确定平均颜色（RGB）

    avg_color = tile.mean(axis=(0, 1))

    if abs(avg_color - np.array([46, 49, 160])).sum() < threshold:
        return 'R'
    elif abs(avg_color - np.array([147, 83, 68])).sum() < threshold:
        return 'B'
    elif abs(avg_color - np.array([57, 138, 174])).sum() < threshold:
        return 'Y'
    elif abs(avg_color - np.array([61, 126, 71])).sum() < threshold:
        return 'G'
    elif abs(avg_color - np.array([156, 99, 125])).sum() < threshold:
        return 'P'
    # elif abs(avg_color - np.array([76, 82, 90])).sum() < threshold:
    #     return 'Z'
    else:
        return '.'

x, y, width, height = get_window_rect("Tumblestone")
screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
# Convert PIL Image to numpy array and ensure it's in the correct format
screen = np.array(screen)
# Convert RGB to BGR (OpenCV format)
screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)  

grid_size = 60
shift = 11

board = [[] for _ in range(5)]
i = 1
j = 3

x = 811 + j * grid_size
y = 160 + i * grid_size
tile = screen[y+shift:y+grid_size-shift, x+shift:x+grid_size-shift]
cv2.imwrite("rbg.png", tile)



c = recognize_tile(tile)
# avg_color = tile.mean(axis=(0, 1))
# print(i, j, *avg_color)




