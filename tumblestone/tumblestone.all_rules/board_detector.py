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

def capture_game_window():
    """捕获游戏窗口"""
    try:
        x, y, width, height = get_window_rect("Tumblestone")
        screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
        screen = np.array(screen)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
        return screen
    except Exception as e:
        print(f"捕获窗口失败: {e}")
        return None

def on_mouse_click(event, x, y, flags, param):
    """鼠标点击回调函数"""
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"点击坐标: ({x}, {y})")
        # 在点击位置画一个红点
        cv2.circle(param['image'], (x, y), 3, (0, 0, 255), -1)
        cv2.imshow("Tumblestone Window", param['image'])

def main():
    # 捕获游戏窗口
    screen = capture_game_window()
    if screen is None:
        return

    # 创建窗口并设置鼠标回调
    cv2.namedWindow("Tumblestone Window")
    cv2.setMouseCallback("Tumblestone Window", on_mouse_click, {'image': screen})
    
    print("请在游戏窗口中点击以下位置来标记游戏区域：")
    print("1. 游戏棋盘的左上角")
    print("2. 游戏棋盘的右下角")
    print("3. 第一个方块的中心位置")
    print("4. 最后一个方块的中心位置")
    print("\n按 'q' 键退出程序")
    
    while True:
        cv2.imshow("Tumblestone Window", screen)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

