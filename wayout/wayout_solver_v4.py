import numpy as np
from typing import List, Tuple, Optional, Set

class WayOutSolver:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.board = None
        self.playable_positions = []  # 存储可玩位置的坐标
        self.pos_to_index = {}  # 位置到索引的映射
        self.index_to_pos = {}  # 索引到位置的映射
        self.group_positions = []  # 存储绑定组格子的位置
        
    def parse_cell(self, cell_str: str) -> Tuple[str, bool]:
        """
        解析格子字符串
        返回：(格子类型, 是否按下)
        """
        cell_str = cell_str.strip()
        if cell_str == 'w':
            return 'wall', False
        elif cell_str in ['n', 'N']:
            return 'normal', cell_str.isupper()
        elif cell_str in ['v', 'V']:
            return 'vertical', cell_str.isupper()
        elif cell_str in ['h', 'H']:
            return 'horizontal', cell_str.isupper()
        elif cell_str in ['c', 'C']:
            return 'cross', cell_str.isupper()
        elif cell_str in ['g', 'G']:
            return 'group', cell_str.isupper()
        else:
            raise ValueError(f"无效的格子类型: {cell_str}")
    
    def setup_board(self, board_input: List[List[str]]):
        """
        设置棋盘
        board_input: 字符串格式的棋盘输入
        """
        self.board = []
        self.playable_positions = []
        self.pos_to_index = {}
        self.index_to_pos = {}
        self.group_positions = []
        
        # 解析棋盘
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                cell_type, is_pressed = self.parse_cell(board_input[i][j])
                row.append((cell_type, is_pressed))
                
                # 收集绑定组格子位置
                if cell_type == 'group':
                    self.group_positions.append((i, j))
            self.board.append(row)
        
        # 找出所有可玩位置（非墙壁）
        index = 0
        for i in range(self.rows):
            for j in range(self.cols):
                if self.board[i][j][0] != 'wall':
                    self.playable_positions.append((i, j))
                    self.pos_to_index[(i, j)] = index
                    self.index_to_pos[index] = (i, j)
                    index += 1
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """检查位置是否有效且不是墙壁"""
        return (0 <= row < self.rows and 
                0 <= col < self.cols and 
                self.board[row][col][0] != 'wall')
    
    def get_direct_neighbors(self, row: int, col: int, cell_type: str) -> List[Tuple[int, int]]:
        """
        获取直接按下按钮时会影响的位置
        """
        affected = []
        
        # 按钮本身
        if self.is_valid_position(row, col):
            affected.append((row, col))
        
        if cell_type in ['normal', 'group']:
            # 普通格子和绑定组格子：影响四个方向
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    affected.append((new_row, new_col))
                    
        elif cell_type == 'vertical':
            # 竖直单一方向格：只影响上下
            directions = [(-1, 0), (1, 0)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    affected.append((new_row, new_col))
                    
        elif cell_type == 'horizontal':
            # 水平单一方向格：只影响左右
            directions = [(0, -1), (0, 1)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    affected.append((new_row, new_col))
                    
        elif cell_type == 'cross':
            # 十字格：按下时影响四个方向（和普通格子一样）
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    affected.append((new_row, new_col))
        
        return affected
    
    def apply_group_effect(self, affected_positions: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        应用绑定组效果：如果绑定组中任何格子被影响，整个组都被影响
        """
        result = affected_positions.copy()
        
        # 检查是否有绑定组格子被影响
        group_affected = False
        for pos in affected_positions:
            if pos in self.group_positions:
                group_affected = True
                break
        
        # 如果绑定组被影响，添加所有绑定组格子
        if group_affected:
            for pos in self.group_positions:
                result.add(pos)
        
        return result
    
    def get_cross_triggered_positions(self, changed_positions: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        计算十字格被触发后额外影响的位置
        """
        additional_changes = set()
        
        for row, col in changed_positions:
            if self.is_valid_position(row, col):
                cell_type, _ = self.board[row][col]
                if cell_type == 'cross':
                    # 十字格状态改变，影响四个邻居
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dr, dc in directions:
                        new_row, new_col = row + dr, col + dc
                        if self.is_valid_position(new_row, new_col):
                            additional_changes.add((new_row, new_col))
        
        return additional_changes
    
    def calculate_total_effect(self, button_row: int, button_col: int) -> Set[Tuple[int, int]]:
        """
        计算按下某个按钮的总效果（包括绑定组效果和十字格的连锁反应）
        """
        if not self.is_valid_position(button_row, button_col):
            return set()
        
        cell_type, _ = self.board[button_row][button_col]
        
        # 第一波：直接影响
        affected = set(self.get_direct_neighbors(button_row, button_col, cell_type))
        
        # 应用绑定组效果
        affected = self.apply_group_effect(affected)
        
        total_affected = affected.copy()
        
        # 处理十字格的连锁反应
        processed_rounds = 0
        max_rounds = 100  # 防止无限循环
        
        while affected and processed_rounds < max_rounds:
            # 计算这一轮十字格触发的额外影响
            new_affected = self.get_cross_triggered_positions(affected)
            
            # 应用绑定组效果到新影响的位置
            new_affected = self.apply_group_effect(new_affected)
            
            # 只保留之前没有被影响过的位置
            new_affected = new_affected - total_affected
            
            if not new_affected:
                break
                
            total_affected.update(new_affected)
            affected = new_affected
            processed_rounds += 1
        
        return total_affected
    
    def create_coefficient_matrix(self) -> np.ndarray:
        """创建系数矩阵A，考虑所有特殊格子的效果"""
        size = len(self.playable_positions)
        matrix = np.zeros((size, size), dtype=int)
        
        for button_idx in range(size):
            button_row, button_col = self.index_to_pos[button_idx]
            
            # 计算按下这个按钮的总效果（包括连锁反应）
            affected_positions = self.calculate_total_effect(button_row, button_col)
            
            for pos_row, pos_col in affected_positions:
                if (pos_row, pos_col) in self.pos_to_index:
                    pos_idx = self.pos_to_index[(pos_row, pos_col)]
                    matrix[pos_idx][button_idx] = 1
        
        return matrix
    
    def solve_gf2_all_solutions(self, matrix: np.ndarray, target: np.ndarray) -> List[np.ndarray]:
        """在GF(2)域上求解线性方程组 Ax = b，返回所有可能的解"""
        if matrix.size == 0:
            return [np.array([])]
            
        # 创建增广矩阵
        augmented = np.hstack([matrix, target.reshape(-1, 1)])
        augmented = augmented.astype(int)
        original_cols = matrix.shape[1]
        
        rows, cols = augmented.shape
        
        # 高斯消元法 (GF(2)) - 化简为行阶梯形
        pivot_row = 0
        pivot_cols = []  # 记录主元列
        
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
            
            pivot_cols.append(col)
            
            # 消元
            for row in range(rows):
                if row != pivot_row and augmented[row, col] == 1:
                    augmented[row] = (augmented[row] + augmented[pivot_row]) % 2
            
            pivot_row += 1
        
        # 检查是否有解
        for row in range(pivot_row, rows):
            if augmented[row, -1] == 1:
                return []  # 无解
        
        # 找出自由变量
        free_vars = []
        for col in range(original_cols):
            if col not in pivot_cols:
                free_vars.append(col)
        
        # 如果没有自由变量，只有一个解
        if not free_vars:
            solution = np.zeros(original_cols, dtype=int)
            
            # 回代求解
            for i in range(len(pivot_cols) - 1, -1, -1):
                pivot_col = pivot_cols[i]
                row = i
                
                value = augmented[row, -1]
                for col in range(pivot_col + 1, original_cols):
                    value = (value + augmented[row, col] * solution[col]) % 2
                solution[pivot_col] = value
            
            return [solution]
        
        # 有自由变量，枚举所有可能的组合
        solutions = []
        num_free = len(free_vars)
        
        # 枚举所有可能的自由变量赋值（2^num_free种）
        for assignment in range(2 ** num_free):
            solution = np.zeros(original_cols, dtype=int)
            
            # 设置自由变量的值
            for i, var in enumerate(free_vars):
                solution[var] = (assignment >> i) & 1
            
            # 回代求解主元变量
            for i in range(len(pivot_cols) - 1, -1, -1):
                pivot_col = pivot_cols[i]
                row = i
                
                value = augmented[row, -1]
                for col in range(pivot_col + 1, original_cols):
                    value = (value + augmented[row, col] * solution[col]) % 2
                solution[pivot_col] = value
            
            solutions.append(solution)
        
        return solutions
    
    def find_minimal_solution(self, solutions: List[np.ndarray]) -> Optional[np.ndarray]:
        """从所有解中找到按钮次数最少的解"""
        if not solutions:
            return None
        
        min_presses = float('inf')
        best_solution = None
        
        for solution in solutions:
            presses = np.sum(solution)
            if presses < min_presses:
                min_presses = presses
                best_solution = solution
        
        return best_solution
    
    def solve(self, board_input: List[List[str]]) -> Optional[List[List[str]]]:
        """
        求解游戏
        board_input: 字符串格式的初始状态
        返回：解决方案，格式与输入相同
        """
        # 设置棋盘
        self.setup_board(board_input)
        
        if not self.playable_positions:
            return [[]]  # 没有可玩位置
        
        # 提取可玩位置的初始状态
        initial_states = []
        for row, col in self.playable_positions:
            _, is_pressed = self.board[row][col]
            initial_states.append(1 if is_pressed else 0)
        initial_array = np.array(initial_states)
        
        # 目标状态（全部按下）
        target_array = np.ones(len(self.playable_positions), dtype=int)
        
        # 计算需要的变化
        change_needed = (target_array - initial_array) % 2
        
        # 创建系数矩阵
        coefficient_matrix = self.create_coefficient_matrix()
        
        # 求解所有可能的解
        all_solutions = self.solve_gf2_all_solutions(coefficient_matrix, change_needed)
        
        if not all_solutions:
            return None
        
        # 找到按钮次数最少的解
        solution = self.find_minimal_solution(all_solutions)
        
        if solution is None:
            return None
        
        # 将解转换为二维字符串数组
        solution_2d = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                cell_type, _ = self.board[i][j]
                if cell_type == 'wall':
                    row.append('w')
                elif (i, j) in self.pos_to_index:
                    idx = self.pos_to_index[(i, j)]
                    if solution[idx] == 1:
                        row.append('X')  # 需要按下
                    else:
                        row.append('.')  # 不需要按下
                else:
                    row.append('.')
            solution_2d.append(row)
        
        return solution_2d
    
    def verify_solution(self, initial_board: List[List[str]], solution: List[List[str]]) -> bool:
        """验证解的正确性"""
        # 重新设置棋盘
        self.setup_board(initial_board)
        
        # 复制当前状态
        current_state = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                cell_type, is_pressed = self.board[i][j]
                row.append((cell_type, is_pressed))
            current_state.append(row)
        
        # 模拟按下按钮的过程
        for i in range(self.rows):
            for j in range(self.cols):
                if solution[i][j] == 'X':  # 需要按下这个按钮
                    if not self.is_valid_position(i, j):
                        continue
                    
                    # 计算按下此按钮的总效果
                    affected_positions = self.calculate_total_effect(i, j)
                    
                    # 应用效果
                    for r, c in affected_positions:
                        if self.is_valid_position(r, c):
                            cell_type, old_state = current_state[r][c]
                            current_state[r][c] = (cell_type, not old_state)
        
        # 检查是否所有非墙壁位置都是按下状态
        for i in range(self.rows):
            for j in range(self.cols):
                cell_type, is_pressed = current_state[i][j]
                if cell_type != 'wall' and not is_pressed:
                    return False
        
        return True

def print_board(board: List[List[str]], title: str):
    """打印棋盘状态"""
    print(f"\n{title}:")
    for row in board:
        print(" ".join(f"{cell:>2}" for cell in row))

def print_legend():
    """打印图例"""
    print("\n=== 格子类型说明 ===")
    print("w     : 墙壁")
    print("n / N : 普通格子（未按下/按下）")
    print("v / V : 竖直单一方向格（未按下/按下）")
    print("h / H : 水平单一方向格（未按下/按下）")
    print("c / C : 十字格（未按下/按下）")
    print("g / G : 绑定组格子（未按下/按下）")
    print("\n=== 解决方案说明 ===")
    print("X : 需要按下这个按钮")
    print(". : 不需要按下")
    print("w : 墙壁")

def test_example():
    """测试包含特殊格子的例子"""
    print("\n=== 测试用例 ===")
    
    # 创建一个包含各种特殊格子的测试棋盘
    test_board = [
        'NnnNN',
        'NnnNN',
        'nNnnN',
        'NnnNN',
        'NNNNn',
    ]
    
    solver = WayOutSolver(len(test_board), len(test_board[0]))
    solution = solver.solve(test_board)
    
    if solution is not None:
        print_board(test_board, "测试初始状态")
        print_board(solution, "测试解决方案")
        
        if solver.verify_solution(test_board, solution):
            print("✓ 测试通过！")
            
            # 显示绑定组信息
            print(f"绑定组包含{len(solver.group_positions)}个格子：{solver.group_positions}")
        else:
            print("✗ 测试失败！")
    else:
        print("测试用例无解")

if __name__ == "__main__":
    test_example()