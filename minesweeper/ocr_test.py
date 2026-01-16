import re
import cv2
import numpy as np
from PIL import ImageGrab
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from get_template import get_window_rect

def parse_code_string(text):
    """
    从可能存在OCR错误的字符串中提取关键信息
    返回：(括号内容列表, 棋盘大小, 第一个数字)
    """
    # 预处理：移除空格
    text = text.replace(" ", "")
    
    # 存储结果
    bracket_contents = []
    board_size = None
    first_number = None
    
    # 1. 查找所有可能的方括号内容
    # 使用宽松的模式，允许各种可能被错误识别的括号
    bracket_pattern = r'[\[I]([A-Z]|@[cC]|1)[\]I1]'
    matches = re.finditer(bracket_pattern, text)
    for match in matches:
        content = match.group(1)
        # 统一 @c 的大小写
        if content.upper() == '@C':
            content = '@c'
        elif content == '1':
            content = 'T'
        bracket_contents.append(content)
    

    # 2. 查找棋盘大小
    # 匹配 5x5, 6x6, 7x7, 8x8 格式，允许小写x
    size_pattern = r'[5-8][xX][5-8]'
    size_match = re.search(size_pattern, text)
    if size_match:
        board_size = size_match.group().replace('X', 'x')
    
    # 3. 在棋盘大小后面查找第一个数字
    if board_size:
        # 找到棋盘大小在原字符串中的位置
        size_pos = text.find(board_size)
        if size_pos != -1:
            # 在棋盘大小后面查找第一串数字
            number_match = re.search(r'\d+', text[size_pos + len(board_size):])
            if number_match:
                first_number = number_match.group()
    
    return bracket_contents, board_size, first_number

def get_info():
    # 获取扫雷窗口的位置和大小
    x, y, width, height = get_window_rect('Minesweeper Variants')

    # 截取指定窗口的画面
    screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
    screen = np.array(screen)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)    

    # 测试游戏信息区域的截取
    info_x = 52  # 左下角文本的x坐标
    info_y = height - 10  # 左下角文本的y坐标
    info_width = 500  # 截取区域的宽度
    info_height = 30  # 截取区域的高度

    cell = screen[info_y - info_height:info_y, info_x:info_x + info_width]

    text = pytesseract.image_to_string(cell, config='--psm 7')
    text = text.replace('II', '][')  # 修正 ][ 被识别成 II 的问题
    return parse_code_string(text)

if __name__ == '__main__':
    # 获取扫雷窗口的位置和大小
    x, y, width, height = get_window_rect('Minesweeper Variants')

    # 截取指定窗口的画面
    screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
    screen = np.array(screen)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # 测试游戏信息区域的截取
    info_x = 52  # 左下角文本的x坐标
    info_y = height - 10  # 左下角文本的y坐标
    info_width = 500  # 截取区域的宽度
    info_height = 30  # 截取区域的高度

    cell = screen[info_y - info_height:info_y, info_x:info_x + info_width]



    text = pytesseract.image_to_string(cell, config='--psm 7')
    text = text.replace('II', '][')  # 修正 ][ 被识别成 II 的问题
    print(text)
    print(parse_code_string(text))

