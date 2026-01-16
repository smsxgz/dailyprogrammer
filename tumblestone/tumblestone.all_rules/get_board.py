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

def load_color_templates():
    """加载颜色模板图片"""
    templates = {}
    color_files = {
        'rgyb': 'rgyb.png',
        'ryb': 'ryb.png',
        'yb': 'yb.png',
        'rbg': 'rbg.png',
        'Z': 'z.png'  # 添加Z方块的模板
    }
    
    for color, filename in color_files.items():
        template_path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(template_path):
            template = cv2.imread(template_path)
            if template is not None:
                templates[color] = template
            else:
                print(f"Warning: Could not load template {filename}")
        else:
            print(f"Warning: Template file {filename} not found")
    
    return templates

def get_board():
    # 加载颜色模板
    color_templates = load_color_templates()
    if not color_templates:
        raise Exception("No color templates loaded")

    x, y, width, height = get_window_rect("Tumblestone")
    screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
    # Convert PIL Image to numpy array and ensure it's in the correct format
    screen = np.array(screen)
    # Convert RGB to BGR (OpenCV format)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)  

    grid_size = 60
    shift = 11

    board = [[] for _ in range(5)]
    i = 0
    while True:
        line = ''
        for j in range(5):
            x = 811 + j * grid_size
            y = 160 + i * grid_size
            tile = screen[y+shift:y+grid_size-shift, x+shift:x+grid_size-shift]
            c = recognize_tile(tile, color_templates)
            line += c
            board[j].append(c)
 
        i += 1
        if line == '.....':
            for j in range(5):
                board[j].pop(-1)
            break

    return '\n'.join([''.join(line) for line in board])

def recognize_tile(tile, color_templates, threshold=25, similarity_threshold=0.65):
    """识别tile的颜色，使用模板匹配来识别万能方块和砖块"""
    # 首先检查是否是已知颜色
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
    
    # 如果不是已知颜色，尝试模板匹配
    max_similarity = 0
    matched_type = None
    
    for color, template in color_templates.items():
        # 使用模板匹配
        result = cv2.matchTemplate(tile, template, cv2.TM_CCOEFF_NORMED)
        similarity = np.max(result)
        
        if similarity > max_similarity:
            max_similarity = similarity
            matched_type = color
    
    # 如果与任何模板的相似度都超过阈值
    # print(max_similarity, matched_type)
    if max_similarity >= similarity_threshold:
        if matched_type == 'Z':
            return 'Z'  # 砖块
        elif matched_type in ['rgyb', 'ryb', 'yb', 'rbg']:
            return 'W'  # 万能方块
    
    return '.'

if __name__ == "__main__":
    print(get_board())

