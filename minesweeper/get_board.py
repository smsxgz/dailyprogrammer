import os
import cv2
import numpy as np
from PIL import ImageGrab
import win32gui
import time
import re
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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

def get_game_board():
    """获取整个游戏棋盘的状态"""
    x, y, width, height = get_window_rect("Minesweeper Variants")
    
    screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
    screen = np.array(screen)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # 获取游戏信息
    info_x, info_y = 52, height - 10
    info_cell = screen[info_y - 30:info_y, info_x:info_x + 500]
    text = pytesseract.image_to_string(info_cell, config='--psm 7')
    text = text.replace('II', '][')
    rule_type, board_size, total_mines = parse_code_string(text)
    board_size = int(board_size[0])
    total_mines = int(total_mines)

    # 为不同大小的棋盘设置不同的起始坐标
    grid_positions = {
        5: (389, 205),
        6: (364, 180),
        7: (339, 155),
        8: (314, 130)
    }
    
    if board_size not in grid_positions:
        raise ValueError(f"不支持的棋盘大小: {board_size}")
        
    gridx, gridy = grid_positions[board_size]
    grid_size, grid_shift = 46, 50
    
    # 识别棋盘
    board = []
    for i in range(board_size):
        row = []
        for j in range(board_size):
            cell = screen[gridy + i * grid_shift:gridy + i * grid_shift + grid_size, 
                        gridx + j * grid_shift:gridx + j * grid_shift + grid_size]
            row.append(recognize_cell_value(cell, rule_type))
        board.append(row)

    return board, rule_type, total_mines

def get_cell_value(row, col, board_size, rule_type):
    """获取指定格子的值"""
    # 获取窗口尺寸
    x, y, width, height = get_window_rect("Minesweeper Variants")
    
    grid_positions = {
        5: (389, 205),
        6: (364, 180),
        7: (339, 155),
        8: (314, 130)
    }
    
    grid_size, grid_shift = 46, 50
    gridx, gridy = grid_positions[board_size]
    
    screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
    screen = np.array(screen)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    cell = screen[gridy + row * grid_shift:gridy + row * grid_shift + grid_size,
                 gridx + col * grid_shift:gridx + col * grid_shift + grid_size]
    
    return recognize_cell_value(cell, rule_type)

def recognize_cell_value(cell, rule_type):
    """识别单个格子的值，当 rule_type 含有 '#' 时识别右下角标识"""
    templates = {
        'question.png': -2,
        'flag.png': -3,
    }
    
    # 加载所有number开头的图片
    for filename in os.listdir('figures'):
        if filename.startswith('number'):
            # 解析文件名
            name = filename[6:-4]  # 去掉'number'前缀和'.png'后缀
            if '_' in name:
                # tuple格式的数字，如 'number1_1_1.png' -> (1,1,1)
                value = tuple(int(n) for n in name.split('_'))
            else:
                # 单个数字，如 'number3.png' -> 3
                value = int(name)
            templates[filename] = value
        
        elif filename.startswith('h'):
            templates[filename] = (int(filename[1:-4]), 'Eh')
        
        elif filename.startswith('v'):
            templates[filename] = (int(filename[1:-4]), 'Ev')
    
    gray_mask = np.all(cell == [76, 76, 76], axis=2)
    cell = cell.copy()
    cell[gray_mask] = [0, 0, 0]

    if '#' in rule_type:
        marker = cell[35:, 30:].copy()
        cell[35:, 30:] = [0, 0, 0]
    
    if np.mean(cell) < 2:
        return -1

    max_score = 0
    best_value = -1
    
    for filename, value in templates.items():
        template = cv2.imread(f'figures/{filename}')
        res = cv2.matchTemplate(cell, template, cv2.TM_CCOEFF_NORMED)
        score = res[0][0]
        if score > max_score:
            max_score = score
            best_value = value

    if max_score < 0.9:
        best_value = -1
    
    if '#' in rule_type and best_value not in [-2, -3]:
        # 提取并处理右下角标识区域
        max_score_marker = 0
        best_marker = None
        
        # 获取右下角标识中最匹配的模板
        for filename in os.listdir('type_figures'):
            template = cv2.imread(f'type_figures/{filename}')
            res = cv2.matchTemplate(marker, template, cv2.TM_CCOEFF_NORMED)
            _, score, _, _ = cv2.minMaxLoc(res)
            if score > max_score_marker:
                max_score_marker = score
                best_marker = os.path.splitext(filename)[0]
        
        if max_score_marker < 0.9:
            best_marker = None
        return best_value, best_marker
    
    return best_value

def parse_code_string(text):
    """从OCR文本中提取游戏信息"""
    text = text.replace(" ", "").strip()
    print(text)
    
    bracket_contents = []
    board_size = None
    first_number = None
    
    # 先找到棋盘大小的位置
    size_pattern = r'[5-8][xX][5-8]'
    size_match = re.search(size_pattern, text)
    if size_match:
        board_size = size_match.group().replace('X', 'x')
        end_position = size_match.start()  # 只处理到这个位置
    else:
        return [], None, None  # 如果没找到棋盘大小，直接返回

    # 只处理棋盘大小之前的文本
    pattern_text = text[:end_position]
    if (len(pattern_text) % 3 == 2 or (len(pattern_text) % 3 == 0 and '@' in pattern_text)) and 'U' in pattern_text:
        pattern_text = pattern_text.replace('U', '][')
    bracket_pattern = r'[\[I1]([A-Z10#]\'?|@[cC])[\]IJ1lU]'
    matches = re.finditer(bracket_pattern, pattern_text)
    for match in matches:
        content = match.group(1)
        if content.upper() == '@C':
            content = '@c'
        elif content == '1':
            content = 'T'
        elif content == '0':
            content = 'O'
        bracket_contents.append(content)
      
    if board_size:
        size_pos = text.find(board_size)
        if size_pos != -1:
            number_match = re.search(r'\d+', text[size_pos + len(board_size):])
            if number_match:
                first_number = number_match.group()
    
    return bracket_contents, board_size, first_number

if __name__ == "__main__":
    # 测试代码
    board, rule_type, total_mines = get_game_board()
    print(board)
    print(rule_type)
    print(total_mines)