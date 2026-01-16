import numpy as np
from typing import List, Tuple, Optional

class WayOutSolver:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.board = None
        self.playable_positions = []  # 存储可玩位置的坐标
        self.pos_to_index = {}  # 位置到索引的映射
        self.index_to_pos = {}  # 索引到位置的映射
        
    def setup_board(self, board: List[List[int]]):
        """
        设置棋盘
        board: 棋盘状态，-1表示墙壁，0表示未按下，1表示按下
        """
        self.board = [row[:] for row in board]  # 深拷贝
        self.playable_positions = []
        self.pos_to_index = {}
        self.index_to_pos = {}
        
        # 找出所有可玩位置（非墙壁）
        index = 0
        for i in range(self.rows):
            for j in range(self.cols):
                if board[i][j] != -1:  # 不是墙壁
                    self.playable_positions.append((i, j))
                    self.pos_to_index[(i, j)] = index
                    self.index_to_pos[index] = (i, j)
                    index += 1
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """检查位置是否有效且不是墙壁"""
        return (0 <= row < self.rows and 
                0 <= col < self.cols and 
                self.board[row][col] != -1)
    
    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """获取指定位置的相邻位置（包括自身，但排除墙壁）"""
        neighbors = []
        
        # 如果当前位置本身是墙壁，则不包括自身
        if self.is_valid_position(row, col):
            neighbors.append((row, col))
        
        # 上下左右四个方向
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                neighbors.append((new_row, new_col))
        
        return neighbors
    
    def create_coefficient_matrix(self) -> np.ndarray:
        """创建系数矩阵A，其中A[i][j]表示按下按钮j是否会影响位置i"""
        size = len(self.playable_positions)
        matrix = np.zeros((size, size), dtype=int)
        
        for button_idx in range(size):
            button_row, button_col = self.index_to_pos[button_idx]
            
            # 获取按下这个按钮会影响的所有位置
            affected_positions = self.get_neighbors(button_row, button_col)
            
            for pos_row, pos_col in affected_positions:
                if (pos_row, pos_col) in self.pos_to_index:
                    pos_idx = self.pos_to_index[(pos_row, pos_col)]
                    matrix[pos_idx][button_idx] = 1
        
        return matrix
    
    def solve_gf2(self, matrix: np.ndarray, target: np.ndarray) -> Optional[np.ndarray]:
        """在GF(2)域上求解线性方程组 Ax = b"""
        if matrix.size == 0:
            return np.array([])
            
        # 创建增广矩阵
        augmented = np.hstack([matrix, target.reshape(-1, 1)])
        augmented = augmented.astype(int)
        
        rows, cols = augmented.shape
        
        # 高斯消元法 (GF(2))
        pivot_row = 0
        for col in range(cols - 1):  # 不包括最后一列（目标向量）
            # 寻找主元
            pivot_found = False
            for row in range(pivot_row, rows):
                if augmented[row, col] == 1:
                    # 交换行
                    if row != pivot_row:
                        augmented[[pivot_row, row]] = augmented[[row, pivot_row]]
                    pivot_found = True
                    break
            
            if not pivot_found:
                continue
            
            # 消元
            for row in range(rows):
                if row != pivot_row and augmented[row, col] == 1:
                    augmented[row] = (augmented[row] + augmented[pivot_row]) % 2
            
            pivot_row += 1
        
        # 检查是否有解
        for row in range(pivot_row, rows):
            if augmented[row, -1] == 1:
                return None  # 无解
        
        # 回代求解
        solution = np.zeros(cols - 1, dtype=int)
        for row in range(min(pivot_row, cols - 1) - 1, -1, -1):
            # 找到这一行的主元列
            pivot_col = -1
            for col in range(cols - 1):
                if augmented[row, col] == 1:
                    pivot_col = col
                    break
            
            if pivot_col != -1:
                # 计算这个变量的值
                value = augmented[row, -1]
                for col in range(pivot_col + 1, cols - 1):
                    value = (value + augmented[row, col] * solution[col]) % 2
                solution[pivot_col] = value
        
        return solution
    
    def solve(self, initial_board: List[List[int]]) -> Optional[List[List[int]]]:
        """
        求解游戏
        initial_board: 初始状态，-1表示墙壁，0表示未按下，1表示按下
        返回：解决方案，-1表示墙壁，0表示不按，1表示按下该按钮
        """
        # 设置棋盘
        self.setup_board(initial_board)
        
        if not self.playable_positions:
            return [[]]  # 没有可玩位置
        
        # 提取可玩位置的初始状态
        initial_states = []
        for row, col in self.playable_positions:
            initial_states.append(initial_board[row][col])
        initial_array = np.array(initial_states)
        
        # 目标状态（全部按下）
        target_array = np.ones(len(self.playable_positions), dtype=int)
        
        # 计算需要的变化
        change_needed = (target_array - initial_array) % 2
        
        # 创建系数矩阵
        coefficient_matrix = self.create_coefficient_matrix()
        
        # 求解
        solution = self.solve_gf2(coefficient_matrix, change_needed)
        
        if solution is None:
            return None
        
        # 将解转换为二维数组
        solution_2d = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                if initial_board[i][j] == -1:  # 墙壁
                    row.append(-1)
                elif (i, j) in self.pos_to_index:
                    idx = self.pos_to_index[(i, j)]
                    row.append(int(solution[idx]))
                else:
                    row.append(0)  # 理论上不应该到达这里
            solution_2d.append(row)
        
        return solution_2d
    
    def verify_solution(self, initial_board: List[List[int]], solution: List[List[int]]) -> bool:
        """验证解的正确性"""
        # 模拟按下按钮的过程
        current_state = [row[:] for row in initial_board]  # 深拷贝
        
        for i in range(self.rows):
            for j in range(self.cols):
                if solution[i][j] == 1:  # 需要按下这个按钮
                    # 获取会被影响的位置
                    affected = self.get_neighbors(i, j)
                    for r, c in affected:
                        if current_state[r][c] != -1:  # 不是墙壁
                            current_state[r][c] = 1 - current_state[r][c]  # 翻转状态
        
        # 检查是否所有非墙壁位置都是按下状态（1）
        for i in range(self.rows):
            for j in range(self.cols):
                if current_state[i][j] != -1 and current_state[i][j] != 1:
                    return False
        
        return True

def print_board(board: List[List[int]], title: str):
    """打印棋盘状态"""
    print(f"\n{title}:")
    for row in board:
        print(" ".join("■" if x == -1 else str(x) for x in row))


# 测试用例
def test_example():
    """测试一个带墙壁的例子"""
    print("\n=== 测试用例 ===")
    
    # 创建一个带墙壁的测试棋盘
    test_board = [
        [0,1,0,1,0],
        [1,0,0,1,1],
        [0,1,0,0,0],
        [0,1,1,1,0],
        [1,0,1,1,1]
    ]
    
    solver = WayOutSolver(5, 5)
    solution = solver.solve(test_board)
    
    if solution is not None:
        print_board(test_board, "测试初始状态")
        print_board(solution, "测试解决方案")
        
        if solver.verify_solution(test_board, solution):
            print("✓ 测试通过！")
        else:
            print("✗ 测试失败！")
    else:
        print("测试用例无解")

if __name__ == "__main__":
    test_example()
