from get_board import get_game_board, get_window_rect, get_cell_value
from solver_z3 import solve_minesweeper
from clicker import click, right_click, move_mouse_away
import time
from solver_z3 import MinesweeperSATSolver


def play_minesweeper(n=10):
    # 获取游戏窗口位置信息
    try:
        x, y, width, height = get_window_rect("Minesweeper Variants")
    except Exception as e:
        print(f"无法找到游戏窗口: {e}")
        return

    # 计算棋盘格子的基准位置
    grid_shift = 50  # 每个格子的间距
    
    # 为不同大小的棋盘设置不同的起始坐标
    grid_positions = {
        5: (389, 205),  # 5x5棋盘的起始坐标
        6: (364, 180),  # 6x6棋盘的起始坐标
        7: (339, 155),  # 7x7棋盘的起始坐标
        8: (314, 130)   # 8x8棋盘的起始坐标
    }
    
    for i in range(n):
        board, rule_type, total_mines = get_game_board()
        board_size = len(board)
        print(board)
        print(rule_type, total_mines)

        base_x = x + grid_positions[board_size][0]
        base_y = y + grid_positions[board_size][1]

        solver = MinesweeperSATSolver(board_size, board_size, total_mines, rule_type)
        
        while True:
            # 找到一个确定的格子
            determined_cell = solver.find_next_determined_cell(board)
            if not determined_cell:
                print("没有找到确定的格子！")
                break

            row, col, is_mine = determined_cell
            # 计算点击位置
            click_x = base_x + col * grid_shift + grid_shift // 2
            click_y = base_y + row * grid_shift + grid_shift // 2
            
            # 执行点击
            if is_mine == 1:
                right_click(click_x, click_y)
                board[row][col] = -3  # 更新本地棋盘状态为已标记地雷
            else:
                click(click_x, click_y)
                board[row][col] = -2  # 暂时标记
            
            move_mouse_away(x, y)
            time.sleep(0.1)

            # 检查是否完成
            if solver.is_solved(board):
                print("游戏胜利！")
                click(x + 589, y + 460)
                move_mouse_away(x, y)
                time.sleep(0.5)
                break
                
            elif not is_mine: # 没有完成的话，需要识别具体格子内容
                # 只获取刚点击的格子的新状态
                new_value = get_cell_value(row, col, board_size, rule_type)
                board[row][col] = new_value  # 更新本地棋盘状态


if __name__ == "__main__":
    play_minesweeper(1) 
