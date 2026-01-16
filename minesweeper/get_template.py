import cv2
import numpy as np
from PIL import ImageGrab
import win32gui
import win32con
import time

def get_window_rect(window_title):
    """获取指定标题窗口的位置和大小"""
    window_handle = win32gui.FindWindow(None, window_title)
    if window_handle == 0:
        raise Exception(f'找不到窗口：{window_title}')
    
    # 将窗口置于前台
    win32gui.SetForegroundWindow(window_handle)
    time.sleep(0.1)
    
    # 获取窗口位置和大小（包括边框）
    rect = win32gui.GetWindowRect(window_handle)
    # 获取客户区域（不包括边框和标题栏）
    client_rect = win32gui.GetClientRect(window_handle)
    # 转换客户区域坐标为屏幕坐标
    pt1 = win32gui.ClientToScreen(window_handle, (0, 0))
    
    x = pt1[0]
    y = pt1[1]
    width = client_rect[2]
    height = client_rect[3]
    
    return (x, y, width, height)

# 为不同大小的棋盘设置不同的起始坐标
grid_positions = {
    5: (389, 205),  # 5x5棋盘的起始坐标
    6: (364, 180),  # 6x6棋盘的起始坐标
    7: (339, 155),  # 7x7棋盘的起始坐标
    8: (314, 130)   # 8x8棋盘的起始坐标
}

# 设置要测试的棋盘大小
board_size = 5

# 获取扫雷窗口的位置和大小
x, y, width, height = get_window_rect('Minesweeper Variants')

# 截取指定窗口的画面
screen = ImageGrab.grab(bbox=(x, y, x+width, y+height))
screen = np.array(screen)
screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

grid_size = 46
grid_shift = 50
gridx, gridy = grid_positions[board_size]

# 测试坐标，可以修改 i 和 j 来获取不同位置的格子
i = 0 # 行号
j = 3 # 列号

# 确保 i 和 j 不超过棋盘大小
if i >= board_size or j >= board_size:
    raise ValueError(f"坐标 ({i}, {j}) 超出了 {board_size}x{board_size} 棋盘范围")

cell = screen[gridy + i * grid_shift:gridy + i * grid_shift + grid_size, 
              gridx + j * grid_shift:gridx + j * grid_shift + grid_size]    

gray_mask = np.all(cell == [76, 76, 76], axis=2)
cell_filtered = cell.copy()
cell_filtered[gray_mask] = [0, 0, 0]

# cv2.imwrite('cell.png', cell)
# cv2.imwrite('number12.png', cell_filtered)

type = cell_filtered[35:,30:]
cv2.imwrite('LM.png', type)




# cv2.imshow('Cell', cell)
# cv2.imshow('Cell Filtered', cell_filtered)
# cv2.waitKey(0)
# cv2.destroyAllWindows()



# for i in range(board_size):
#     for j in range(board_size):
#         # 确保 i 和 j 不超过棋盘大小
#         if i >= board_size or j >= board_size:
#             raise ValueError(f"坐标 ({i}, {j}) 超出了 {board_size}x{board_size} 棋盘范围")


#         cell = screen[gridy + i * grid_shift:gridy + i * grid_shift + grid_size, 
#                     gridx + j * grid_shift:gridx + j * grid_shift + grid_size]  
        
#         print(i, j, cell.mean())
