import win32api
import win32con
import time

def click(x, y):
    """在指定坐标处执行鼠标左键点击"""
    win32api.SetCursorPos((x, y))
    time.sleep(0.1)  # 稍微延迟以确保鼠标移动到位
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)  # 短暂延迟
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def right_click(x, y):
    """在指定坐标处执行鼠标右键点击"""
    win32api.SetCursorPos((x, y))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

def move_mouse_away(x=0, y=0):
    """
    将鼠标移动到指定位置，默认移到屏幕左上角
    Args:
        x: 目标x坐标，默认为0
        y: 目标y坐标，默认为0
    """
    win32api.SetCursorPos((x, y))

