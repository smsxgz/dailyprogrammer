from z3 import *

# 计算每个未知格子到最近线索的曼哈顿距离
def manhattan_distance(cell1, cell2):
    return abs(cell1[0] - cell2[0]) + abs(cell1[1] - cell2[1])

class MinesweeperSATSolver:
    def __init__(self, height, width, total_mines, rule_type=['V']):
        self.height = height
        self.width = width
        self.total_mines = total_mines
        self.rule_type = rule_type
        # 创建布尔变量矩阵
        self.cells = [[Bool(f"cell_{i}_{j}") for j in range(width)] 
                     for i in range(height)]           
    
    def get_neighbors(self, row, col):
        """获取相邻格子"""
        neighbors = []
        for i in range(max(0, row-1), min(self.height, row+2)):
            for j in range(max(0, col-1), min(self.width, col+2)):
                if i != row or j != col:
                    neighbors.append((i, j))
        return neighbors
    
    def get_cross_neighbors(self, row, col, distance=2):
        """获取十字形范围内的格子"""
        neighbors = []
        # 检查上下方向
        for i in range(max(0, row-distance), min(self.height, row+distance+1)):
            if i != row:
                neighbors.append((i, col))
        # 检查左右方向
        for j in range(max(0, col-distance), min(self.width, col+distance+1)):
            if j != col:
                neighbors.append((row, j))
        return neighbors
    
    def get_knight_neighbors(self, row, col):
        """获取马步位置的格子"""
        neighbors = []
        moves = [
            (-2, -1), (-2, 1),  # 上两格左右
            (-1, -2), (-1, 2),  # 左右两格向上
            (1, -2), (1, 2),    # 左右两格向下
            (2, -1), (2, 1)     # 下两格左右
        ]
        for dr, dc in moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.height and 0 <= new_col < self.width:
                neighbors.append((new_row, new_col))
        return neighbors
    
    def sum_mines(self, cells, type=['V'], positions=None):
        """计算一组格子中地雷的数量
        positions: 格子位置列表，用于M规则判断是否需要加倍计算"""
        if positions and 'M' in type:
            # 对于M规则，染色格子的地雷计数翻倍
            return Sum([If(cell, 2 if (i + j) % 2 == 1 else 1, 0) 
                       for cell, (i, j) in zip(cells, positions)])
        return Sum([If(cell, 1, 0) for cell in cells])
    
    def is_solved(self, board):
        """检查游戏是否已经完成"""
        unknown_count = sum(1 for i in range(self.height) 
                        for j in range(self.width) if board[i][j] == -1)
        mine_count = sum(1 for i in range(self.height) 
                        for j in range(self.width) if board[i][j] == -3)
        return mine_count == self.total_mines and unknown_count == 0

    def get_ordered_neighbors(self, row, col):
        """获取顺时针排序的8个邻居位置，不存在的位置返回None"""
        neighbors = []
        # 从右上开始顺时针
        directions = [(-1,1), (0,1), (1,1), (1,0), 
                    (1,-1), (0,-1), (-1,-1), (-1,0)]
        for di, dj in directions:
            ni, nj = row + di, col + dj
            if 0 <= ni < self.height and 0 <= nj < self.width:
                neighbors.append((ni, nj))
            else:
                neighbors.append(None)
        return neighbors

    def create_basic_formula(self, board):
        """根据当前棋盘状态创建约束"""
        solver = Solver()
        
        # 添加总地雷数约束 (注意：M规则不影响实际地雷数)
        all_cells = [self.cells[i][j] for i in range(self.height) 
                    for j in range(self.width)]
        solver.add(self.sum_mines(all_cells) == self.total_mines)
        
        # 添加已知格子的约束
        for i in range(self.height):
            for j in range(self.width):
                if board[i][j] == -3:  # 已标记为地雷
                    solver.add(self.cells[i][j])
                elif board[i][j] == -2 or (isinstance(board[i][j], int) and board[i][j] >= 0) or isinstance(board[i][j], tuple):  # 已知不是地雷
                    solver.add(Not(self.cells[i][j]))
                    
                    if (isinstance(board[i][j], int) and board[i][j] >= 0) or isinstance(board[i][j], tuple):  # 数字格子或tuple格子
                        if '#' in self.rule_type:
                            # 检查是否是带规则类型的线索
                            assert isinstance(board[i][j], tuple) and len(board[i][j]) == 2
                            clue, rule = board[i][j]
                            if clue == -2 and rule is None:
                                continue
                            # self.add_clue_constraints(solver, clue, [rule], i, j)
                            self.add_clue_constraints(solver, clue, rule, i, j)
                        else:
                            self.add_clue_constraints(solver, board[i][j], self.rule_type, i, j)
                        
        # 添加马步反规则的约束
        if 'A' in self.rule_type:
            for i in range(self.height):
                for j in range(self.width):
                    knight_neighbors = self.get_knight_neighbors(i, j)
                    # 对于每个马步可达的格子，添加约束：不能同时为地雷
                    for ni, nj in knight_neighbors:
                        # 只处理一个方向避免重复约束
                        if ni > i:
                            solver.add(Not(And(self.cells[i][j], self.cells[ni][nj])))
        
        # 根据规则类型添加额外约束
        if 'Q' in self.rule_type:
            self.add_2x2_constraints(solver)
        if 'T' in self.rule_type:
            self.add_no_three_consecutive_mines_constraints(solver)
        if 'B' in self.rule_type:
            # 检查总地雷数是否能被行数整除
            if self.total_mines % self.height != 0:
                raise ValueError("使用B规则时，总地雷数必须能被行数整除")
            self.add_balanced_mines_constraints(solver)       
        if 'D' in self.rule_type:
            if self.total_mines % 2 != 0:
                raise ValueError("使用D规则时，总地雷数必须是偶数")
            self.add_domino_constraints(solver)
        if 'D\'' in self.rule_type:
            self.add_strip_constraints(solver)
        if 'S' in self.rule_type:
            self.add_snake_constraints(solver)
        if 'C' in self.rule_type:
            self.add_connectivity_constraints(solver)
        if 'O' in self.rule_type:
            self.add_outer_connectivity_constraints(solver, board)

        # 添加三连规则的约束
        if 'T\'' in self.rule_type:
            for i in range(self.height):
                for j in range(self.width):
                    # 如果这个格子是地雷，那么它必须是某个三连的一部分
                    solver.add(Implies(
                        self.cells[i][j],
                        self.check_triple_line(i, j)
                    ))
        
        # 添加横向不相邻规则的约束
        if 'H' in self.rule_type:
            for i in range(self.height):
                for j in range(self.width - 1):  # 最后一列不需要检查右边
                    # 当前格子和其右边的格子不能同时为地雷
                    solver.add(Not(And(self.cells[i][j], self.cells[i][j + 1])))
        
        if 'U' in self.rule_type:
            for i in range(self.height):
                for j in range(self.width):
                    # 当前格子和其右边和下边的格子不能同时为地雷
                    if j + 1 < self.width:
                        solver.add(Not(And(self.cells[i][j], self.cells[i][j + 1])))
                    if i + 1 < self.height:
                        solver.add(Not(And(self.cells[i][j], self.cells[i + 1][j])))
        
        return solver
    
    def add_clue_constraints(self, solver, clue, rule, i, j):
        neighbors = self.get_neighbors(i, j)
        neighbor_cells = [self.cells[ni][nj] for ni, nj in neighbors]
        
        if 'P' in rule:
            self.add_mine_groups_constraints(solver, clue, i, j)
        
        elif 'W' in rule:
            # 将单个数字转换为tuple
            group_sizes = (clue,) if isinstance(clue, int) else clue
            self.add_mine_groups_size_constraints(solver, list(group_sizes), i, j)
        
        elif 'W\'' in rule:
            self.add_max_mine_group_constraints(solver, clue, i, j)
        
        elif 'E' in rule:
            # E规则：数字表示四个方向上可见的非地雷格子数（包括自己）
            visible_cells = []
            
            # 向上
            up_cells = [(row, j) for row in range(i, -1, -1)]
            for idx, (row, col) in enumerate(up_cells):
                if idx == 0:  # 中心格子
                    visible_cells.append(Not(self.cells[row][col]))
                else:
                    # 只有前面的格子都不是地雷，且当前格子不是地雷时才可见
                    blocking = [self.cells[r][j] for r, _ in up_cells[1:idx]]
                    visible_cells.append(And(Not(Or(blocking)), Not(self.cells[row][col])))
            
            # 向下
            down_cells = [(row, j) for row in range(i, self.height)]
            for idx, (row, col) in enumerate(down_cells):
                if idx == 0:  # 中心格子已计算
                    continue
                blocking = [self.cells[r][j] for r, _ in down_cells[1:idx]]
                visible_cells.append(And(Not(Or(blocking)) if blocking else True, Not(self.cells[row][col])))
            
            # 向左
            left_cells = [(i, col) for col in range(j, -1, -1)]
            for idx, (row, col) in enumerate(left_cells):
                if idx == 0:  # 中心格子已计算
                    continue
                blocking = [self.cells[i][c] for _, c in left_cells[1:idx]]
                visible_cells.append(And(Not(Or(blocking)) if blocking else True, Not(self.cells[row][col])))
            
            # 向右
            right_cells = [(i, col) for col in range(j, self.width)]
            for idx, (row, col) in enumerate(right_cells):
                if idx == 0:  # 中心格子已计算
                    continue
                blocking = [self.cells[i][c] for _, c in right_cells[1:idx]]
                visible_cells.append(And(Not(Or(blocking)) if blocking else True, Not(self.cells[row][col])))
            
            # 计算所有可见的非地雷格子数量
            solver.add(Sum([If(cell, 1, 0) for cell in visible_cells]) == clue)
        
        elif 'E\'' in rule:
            # E'规则：横向和纵向可见非地雷格子数的差值
            horizontal_visible = []  # 横向可见的格子
            vertical_visible = []    # 纵向可见的格子
            
            # 计算水平方向可见格子
            # 1. 中心格子
            horizontal_visible.append(Not(self.cells[i][j]))
            
            # 2. 向右看
            for col in range(j + 1, self.width):
                # 检查从中心到当前位置是否有阻挡
                conditions = []
                # 当前格子不是地雷
                conditions.append(Not(self.cells[i][col]))
                # 中间没有地雷阻挡
                for k in range(j + 1, col):
                    conditions.append(Not(self.cells[i][k]))
                horizontal_visible.append(And(conditions))
            
            # 3. 向左看
            for col in range(j - 1, -1, -1):
                conditions = []
                conditions.append(Not(self.cells[i][col]))
                for k in range(col + 1, j):
                    conditions.append(Not(self.cells[i][k]))
                horizontal_visible.append(And(conditions))
            
            # 计算垂直方向可见格子
            # 1. 中心格子
            vertical_visible.append(Not(self.cells[i][j]))
            
            # 2. 向下看
            for row in range(i + 1, self.height):
                conditions = []
                conditions.append(Not(self.cells[row][j]))
                for k in range(i + 1, row):
                    conditions.append(Not(self.cells[k][j]))
                vertical_visible.append(And(conditions))
            
            # 3. 向上看
            for row in range(i - 1, -1, -1):
                conditions = []
                conditions.append(Not(self.cells[row][j]))
                for k in range(row + 1, i):
                    conditions.append(Not(self.cells[k][j]))
                vertical_visible.append(And(conditions))
            
            # 计算每个方向可见的非地雷格子数
            horizontal_count = Sum([If(cond, 1, 0) for cond in horizontal_visible])
            vertical_count = Sum([If(cond, 1, 0) for cond in vertical_visible])
            
            # 根据Eh/Ev添加约束
            if isinstance(clue, tuple):
                value, direction = clue
                if direction == 'Eh':  # 横向比纵向多value个
                    solver.add(horizontal_count == vertical_count + value)
                elif direction == 'Ev':  # 纵向比横向多value个
                    solver.add(vertical_count == horizontal_count + value)
            # elif clue == 0:
            #     solver.add(horizontal_count == vertical_count)
            else:
                raise ValueError("E'规则必须使用(value, direction)格式的线索")
            
        elif 'K' in rule:
            # K规则：数字表示马步位置的地雷数
            knight_neighbors = self.get_knight_neighbors(i, j)
            knight_cells = [self.cells[ni][nj] for ni, nj in knight_neighbors]
            solver.add(self.sum_mines(knight_cells) == clue)
        
        elif 'N' in rule:
            # N规则：数字表示相邻染色格和非染色格的地雷数之差的绝对值
            colored_cells, colored_neighbors = [], []
            uncolored_cells, uncolored_neighbors = [], []

            if 'X' in rule or 'X\'' in rule:
                distance = 2 if 'X' in rule else 1
                neighbors = self.get_cross_neighbors(i, j, distance)

            for ni, nj in neighbors:
                if (ni + nj) % 2 == 1:  # 染色格
                    colored_cells.append(self.cells[ni][nj])
                    colored_neighbors.append((ni, nj))
                else:  # 非染色格
                    uncolored_cells.append(self.cells[ni][nj])
                    uncolored_neighbors.append((ni, nj))

            # 计算两种格子的地雷数
            colored_sum = self.sum_mines(colored_cells, rule, colored_neighbors)
            uncolored_sum = self.sum_mines(uncolored_cells, rule, uncolored_neighbors)
            
            if clue == 0:
                # 如果提示数字为0，则染色格和非染色格的地雷数必须相等
                solver.add(colored_sum == uncolored_sum)
            else:
                # 其他情况：添加绝对值差等于提示数字的约束
                solver.add(Or(
                    colored_sum - uncolored_sum == clue,
                    uncolored_sum - colored_sum == clue
                ))
        
        elif ('X' in rule or 'X\'' in rule) and 'N' not in rule:
            # X规则：数字表示十字形2格范围内的地雷数
            distance = 2 if 'X' in rule else 1
            cross_neighbors = self.get_cross_neighbors(i, j, distance)
            cross_cells = [self.cells[ni][nj] for ni, nj in cross_neighbors]
            solver.add(self.sum_mines(cross_cells, rule, cross_neighbors) == clue)

        
        elif 'L' in rule:
            # L规则：实际地雷数可能比显示数字多1或少1
            actual_mines = self.sum_mines(neighbor_cells, rule, neighbors)
            possible_values = []
            
            if clue > 0:
                possible_values.append(actual_mines == clue - 1)
            possible_values.append(actual_mines == clue + 1)
            
            solver.add(Or(possible_values))
        
        else:
            solver.add(self.sum_mines(neighbor_cells, rule, neighbors) == clue)

    # def find_determined_cells(self, board):
    #     """找出所有可以确定状态的格子"""

    #     solver = self.create_basic_formula(board)
    #     determined_cells = []  # 存储确定的格子及其状态
    #     unknown_count = sum(1 for i in range(self.height) 
    #                       for j in range(self.width) if board[i][j] == -1)
    #     determined_count = 0
        
    #     # 检查每个未知格子
    #     for i in range(self.height):
    #         for j in range(self.width):
    #             if board[i][j] == -1:  # 未揭示的格子
    #                 # 尝试假设是地雷
    #                 s1 = Solver()
    #                 s1.add(solver.assertions())
    #                 s1.add(self.cells[i][j])
    #                 mine_status = s1.check()
                    
    #                 # 尝试假设不是地雷
    #                 s2 = Solver()
    #                 s2.add(solver.assertions())
    #                 s2.add(Not(self.cells[i][j]))
    #                 safe_status = s2.check()

    #                 # 根据结果判断格子状态
    #                 if mine_status == sat and safe_status == unsat:
    #                     determined_cells.append((i, j, 1))  # 1表示地雷
    #                     determined_count += 1
    #                     print(f"发现确定的地雷位置: ({i},{j})")
    #                 elif mine_status == unsat and safe_status == sat:
    #                     determined_cells.append((i, j, 0))  # 0表示安全
    #                     determined_count += 1
    #                     print(f"发现确定的安全位置: ({i},{j})")
    #                 elif mine_status == unsat and safe_status == unsat:
    #                     raise ValueError("出现矛盾！")
    #     return determined_cells, determined_count == unknown_count

    def add_2x2_constraints(self, solver):
        """添加2x2区域至少一个雷的约束"""
        for i in range(self.height - 1):
            for j in range(self.width - 1):
                # 获取2x2区域内的格子
                square_cells = [
                    self.cells[i][j],
                    self.cells[i][j+1],
                    self.cells[i+1][j],
                    self.cells[i+1][j+1]
                ]
                # 添加至少一个雷的约束
                solver.add(self.sum_mines(square_cells) >= 1)
    
    def add_no_three_consecutive_mines_constraints(self, solver):
        """添加不能有三连雷的约束"""
        # 检查水平方向
        for i in range(self.height):
            for j in range(self.width - 2):
                solver.add(Not(And(self.cells[i][j], 
                                 self.cells[i][j+1], 
                                 self.cells[i][j+2])))
        
        # 检查垂直方向
        for i in range(self.height - 2):
            for j in range(self.width):
                solver.add(Not(And(self.cells[i][j], 
                                 self.cells[i+1][j], 
                                 self.cells[i+2][j])))
        
        # 检查主对角线方向
        for i in range(self.height - 2):
            for j in range(self.width - 2):
                solver.add(Not(And(self.cells[i][j], 
                                 self.cells[i+1][j+1], 
                                 self.cells[i+2][j+2])))
        
        # 检查副对角线方向
        for i in range(self.height - 2):
            for j in range(2, self.width):
                solver.add(Not(And(self.cells[i][j], 
                                 self.cells[i+1][j-1], 
                                 self.cells[i+2][j-2])))

    def add_balanced_mines_constraints(self, solver):
        """添加每行每列雷数相等的约束"""
        # 计算每行应该有的地雷数（总地雷数除以行数）
        mines_per_line = self.total_mines // self.height
        
        # 确保每行的地雷数相等
        for i in range(self.height):
            row_cells = [self.cells[i][j] for j in range(self.width)]
            solver.add(self.sum_mines(row_cells) == mines_per_line)
        
        # 确保每列的地雷数相等
        for j in range(self.width):
            col_cells = [self.cells[i][j] for i in range(self.height)]
            solver.add(self.sum_mines(col_cells) == mines_per_line)
        
    def add_domino_constraints(self, solver):
        """添加多米诺约束：每个地雷格子上下左右必须有且只有一个相邻的地雷"""
        for i in range(self.height):
            for j in range(self.width):
                # 获取当前格子上下左右的相邻格子
                neighbors = []
                if i > 0:  # 上
                    neighbors.append(self.cells[i-1][j])
                if i < self.height - 1:  # 下
                    neighbors.append(self.cells[i+1][j])
                if j > 0:  # 左
                    neighbors.append(self.cells[i][j-1])
                if j < self.width - 1:  # 右
                    neighbors.append(self.cells[i][j+1])
                
                # 如果当前格子是地雷，则其相邻格子中必须恰好有一个是地雷
                if neighbors:  # 确保有相邻格子
                    solver.add(Implies(self.cells[i][j], 
                                     PbEq([(neighbor, 1) for neighbor in neighbors], 1)))
    
    def check_triple_line(self, row, col):
        """检查某个位置是否可能成为三连的一部分"""
        directions = [
            [(0, 1)],      # 水平向右
            [(1, 0)],      # 垂直向下
            [(1, 1)],      # 主对角线向右下
            [(1, -1)]      # 副对角线向左下
        ]
        
        conditions = []
        for dir in directions:
            d = dir[0]
            # 检查三种可能的三连位置
            # 1. 当前格子作为起点
            if (0 <= row + d[0]*2 < self.height and 
                0 <= col + d[1]*2 < self.width):
                conditions.append(And(
                    self.cells[row + d[0]][col + d[1]],
                    self.cells[row + d[0]*2][col + d[1]*2]
                ))
            # 2. 当前格子作为中间点
            if (0 <= row - d[0] < self.height and 
                0 <= col - d[1] < self.width and
                0 <= row + d[0] < self.height and 
                0 <= col + d[1] < self.width):
                conditions.append(And(
                    self.cells[row - d[0]][col - d[1]],
                    self.cells[row + d[0]][col + d[1]]
                ))
            # 3. 当前格子作为终点
            if (0 <= row - d[0]*2 < self.height and 
                0 <= col - d[1]*2 < self.width):
                conditions.append(And(
                    self.cells[row - d[0]][col - d[1]],
                    self.cells[row - d[0]*2][col - d[1]*2]
                ))
        
        return Or(conditions) if conditions else False
    
    # def add_snake_constraints(self, solver):
    #     """添加S规则约束：雷区域组成一条不接触自身的蛇形"""
    #     # 创建变量表示每个地雷格子是否只有一个十字相邻的地雷
    #     has_one_neighbor = [[Bool(f"one_neighbor_{i}_{j}") for j in range(self.width)]
    #                        for i in range(self.height)]
        
    #     # 创建距离变量（到蛇头的距离）
    #     distances = [[Int(f"snake_dist_{i}_{j}") for j in range(self.width)]
    #                 for i in range(self.height)]
        
    #     # 对每个格子添加约束
    #     for i in range(self.height):
    #         for j in range(self.width):
    #             # 获取十字相邻的格子
    #             cross_neighbors = self.get_cross_neighbors(i, j, distance=1)
    #             neighbor_cells = [self.cells[ni][nj] for ni, nj in cross_neighbors]
    #             neighbor_sum = self.sum_mines(neighbor_cells)
                
    #             # 如果当前格子不是地雷，其距离为-1
    #             solver.add(Implies(Not(self.cells[i][j]), distances[i][j] == -1))
                
    #             # 如果当前格子是地雷：
    #             solver.add(Implies(self.cells[i][j], And(
    #                 # 1. 距离必须合法
    #                 distances[i][j] >= 0,
    #                 distances[i][j] < self.total_mines,
    #                 # 2. 相邻地雷数必须是1（头尾）或2（身体）
    #                 And(neighbor_sum >= 1, neighbor_sum <= 2)
    #             )))
                
    #             # 设置has_one_neighbor变量（标识蛇的头尾）
    #             solver.add(has_one_neighbor[i][j] == And(
    #                 self.cells[i][j],
    #                 neighbor_sum == 1
    #             ))
                
    #             # 如果是地雷且不是蛇头，其距离必须是某个相邻地雷格子的距离+1
    #             neighbor_conditions = []
    #             for ni, nj in cross_neighbors:
    #                 neighbor_conditions.append(And(
    #                     self.cells[ni][nj],
    #                     distances[i][j] == distances[ni][nj] + 1
    #                 ))
                
    #             solver.add(Implies(
    #                 And(self.cells[i][j], Not(has_one_neighbor[i][j])),
    #                 Or(*neighbor_conditions)
    #             ))
        
    #     # 确保恰好有两个末端（蛇头和蛇尾）
    #     all_one_neighbor = [has_one_neighbor[i][j] 
    #                     for i in range(self.height) 
    #                     for j in range(self.width)]
    #     solver.add(Sum([If(x, 1, 0) for x in all_one_neighbor]) == 2)
        
    #     # 确保蛇头的距离为0
    #     solver.add(Or(*[
    #         And(has_one_neighbor[i][j], distances[i][j] == 0)
    #         for i in range(self.height)
    #         for j in range(self.width)
    #     ]))
        
    #     # 确保所有地雷格子都是连通的
    #     for i in range(self.height):
    #         for j in range(self.width):
    #             # 如果是地雷格子，必须和至少一个相邻的地雷格子相连
    #             solver.add(Implies(
    #                 And(self.cells[i][j], Not(has_one_neighbor[i][j])),
    #                 Or(*[self.cells[ni][nj] for ni, nj in cross_neighbors])
    #             ))
    def add_snake_constraints(self, solver):
        """添加S规则约束：雷区域组成一条不接触自身的蛇形"""
        # 创建变量表示每个地雷格子是否只有一个十字相邻的地雷
        has_one_neighbor = [[Bool(f"one_neighbor_{i}_{j}") for j in range(self.width)]
                        for i in range(self.height)]
        
        # 创建距离变量（到蛇头的距离）
        distances = [[Int(f"snake_dist_{i}_{j}") for j in range(self.width)]
                    for i in range(self.height)]
        
        # 对每个格子添加约束
        for i in range(self.height):
            for j in range(self.width):
                # 获取十字相邻的格子
                cross_neighbors = self.get_cross_neighbors(i, j, distance=1)
                neighbor_cells = [self.cells[ni][nj] for ni, nj in cross_neighbors]
                neighbor_sum = self.sum_mines(neighbor_cells)
                
                # 非地雷格子的距离为-1
                solver.add(Implies(Not(self.cells[i][j]), distances[i][j] == -1))
                
                # 地雷格子的基本约束
                solver.add(Implies(self.cells[i][j], And(
                    distances[i][j] >= 0,
                    distances[i][j] < self.total_mines,
                    neighbor_sum >= 1,
                    neighbor_sum <= 2
                )))
                
                # 设置has_one_neighbor变量（标识蛇的头尾）
                solver.add(has_one_neighbor[i][j] == And(
                    self.cells[i][j],
                    neighbor_sum == 1
                ))
                
                # 非蛇头格子的距离约束
                neighbor_conditions = []
                for ni, nj in cross_neighbors:
                    neighbor_conditions.append(And(
                        self.cells[ni][nj],
                        distances[i][j] == distances[ni][nj] + 1
                    ))
                
                solver.add(Implies(
                    And(self.cells[i][j], Not(has_one_neighbor[i][j])),
                    And(
                        Or(*neighbor_conditions),
                        distances[i][j] > 0
                    )
                ))
        
        # 确保恰好有两个末端（蛇头和蛇尾）
        all_one_neighbor = [has_one_neighbor[i][j] 
                        for i in range(self.height) 
                        for j in range(self.width)]
        solver.add(Sum([If(x, 1, 0) for x in all_one_neighbor]) == 2)
        
        # 确保有且仅有一个蛇头（距离为0的格子）
        solver.add(And(
            Or(*[
                And(has_one_neighbor[i][j], distances[i][j] == 0)
                for i in range(self.height)
                for j in range(self.width)
            ]),
            *[Implies(
                And(self.cells[i][j], Not(distances[i][j] == 0)),
                distances[i][j] > 0
            ) for i in range(self.height) for j in range(self.width)]
        ))
        
        # 添加连通性和防止自交叉的约束
        for i in range(self.height):
            for j in range(self.width):
                if i > 0:  # 检查上方连接
                    solver.add(Implies(
                        And(self.cells[i][j], self.cells[i-1][j]),
                        Or(
                            distances[i][j] == distances[i-1][j] + 1,
                            distances[i-1][j] == distances[i][j] + 1
                        )
                    ))
                if j > 0:  # 检查左方连接
                    solver.add(Implies(
                        And(self.cells[i][j], self.cells[i][j-1]),
                        Or(
                            distances[i][j] == distances[i][j-1] + 1,
                            distances[i][j-1] == distances[i][j] + 1
                        )
                    ))
        for i in range(self.height - 1):
            for j in range(self.width - 1):
                solver.add(Not(And(
                    self.cells[i][j],
                    self.cells[i+1][j+1],
                    self.cells[i][j+1],
                    self.cells[i+1][j]
                )))


    def add_connectivity_constraints(self, solver):
        """添加连通性约束"""
        # 创建变量表示每个格子的距离（到根的最短路径长度）
        distances = [[Int(f"dist_{i}_{j}") for j in range(self.width)]
                    for i in range(self.height)]
        # 创建根节点变量
        root = [[Bool(f"root_{i}_{j}") for j in range(self.width)]
                for i in range(self.height)]
        
        # 1. 必须有且仅有一个根节点，且根节点必须是地雷
        root_conditions = []
        for i in range(self.height):
            for j in range(self.width):
                root_conditions.append(root[i][j])
                solver.add(Implies(root[i][j], self.cells[i][j]))
        solver.add(Sum([If(r, 1, 0) for r in root_conditions]) == 1)
        
        # 2. 设置距离约束
        for i in range(self.height):
            for j in range(self.width):
                # 根节点距离为0
                solver.add(Implies(root[i][j], distances[i][j] == 0))
                # 非根节点的约束
                solver.add(Implies(And(self.cells[i][j], Not(root[i][j])), 
                    And(distances[i][j] > 0, distances[i][j] <= self.total_mines)))
                # 非地雷格子的距离为-1
                solver.add(Implies(Not(self.cells[i][j]), distances[i][j] == -1))
        
        # 3. 每个非根地雷的距离必须是某个相邻地雷的距离+1
        for i in range(self.height):
            for j in range(self.width):
                neighbors = self.get_neighbors(i, j)
                neighbor_conditions = []
                for ni, nj in neighbors:
                    # 相邻的地雷的距离必须比当前小1
                    neighbor_conditions.append(
                        And(self.cells[ni][nj], 
                            distances[i][j] == distances[ni][nj] + 1))
                solver.add(Implies(And(self.cells[i][j], Not(root[i][j])),
                                 Or(*neighbor_conditions)))
    
    def add_outer_connectivity_constraints(self, solver, board):
        """添加非雷格十字相连的单连通约束"""
        # 非雷格的连通性变量
        safe_distances = [[Int(f"safe_dist_{i}_{j}") for j in range(self.width)]
                        for i in range(self.height)]
        # 雷格的连通性变量
        mine_distances = [[Int(f"mine_dist_{i}_{j}") for j in range(self.width)]
                        for i in range(self.height)]
        
        # 找一个已知的非雷格作为根
        root_i, root_j = None, None
        for i in range(self.height):
            for j in range(self.width):
                if board[i][j] == -2 or (isinstance(board[i][j], int) and board[i][j] >= 0) or isinstance(board[i][j], tuple):
                    root_i, root_j = i, j
                    break
            if root_i is not None:
                break
        
        # 1. 非雷格连通性约束
        # 根节点距离为0
        solver.add(safe_distances[root_i][root_j] == 0)
        for i in range(self.height):
            for j in range(self.width):
                # 非雷格且非根节点：距离为正
                solver.add(Implies(
                    And(Not(self.cells[i][j]), Not(And(i == root_i, j == root_j))),
                    And(safe_distances[i][j] > 0, 
                        safe_distances[i][j] <= self.height * self.width - self.total_mines)))
                # 雷格：距离为-1
                solver.add(Implies(self.cells[i][j], safe_distances[i][j] == -1))
                
                # 每个非根非雷格必须通过十字相邻的非雷格连到根
                if (i != root_i or j != root_j):
                    neighbors = self.get_cross_neighbors(i, j, 1)
                    neighbor_conditions = []
                    for ni, nj in neighbors:
                        neighbor_conditions.append(
                            And(Not(self.cells[ni][nj]),
                                safe_distances[i][j] == safe_distances[ni][nj] + 1))
                    solver.add(Implies(Not(self.cells[i][j]), 
                                    Or(*neighbor_conditions)))
        
        # 2. 雷格连通性约束
        found_root = False
        # 边界上的雷格距离为0
        for i in range(self.height):
            for j in range(self.width):
                is_edge = (i == 0 or i == self.height-1 or 
                        j == 0 or j == self.width-1)
                # 如果这个格子是雷格且在边界上
                solver.add(Implies(And(self.cells[i][j], is_edge),
                                mine_distances[i][j] == 0))
                # 非雷格距离为-1
                solver.add(Implies(Not(self.cells[i][j]),
                                mine_distances[i][j] == -1))
                # 非边界雷格：距离为正
                solver.add(Implies(And(self.cells[i][j], Not(is_edge)),
                    And(mine_distances[i][j] > 0, 
                        mine_distances[i][j] <= self.height * self.width)))
                
                # 每个非边界雷格必须通过十字相邻的雷格连到边界
                if not is_edge:
                    neighbors = self.get_cross_neighbors(i, j, 1)
                    neighbor_conditions = []
                    for ni, nj in neighbors:
                        neighbor_conditions.append(
                            And(self.cells[ni][nj],
                                mine_distances[i][j] == mine_distances[ni][nj] + 1))
                    solver.add(Implies(self.cells[i][j], 
                                    Or(*neighbor_conditions)))
    
    def add_mine_groups_constraints(self, solver, n, i, j):
        """添加连续雷组数的约束"""
        neighbors = self.get_ordered_neighbors(i, j)

        # 特殊处理: 如果提示数字为0，所有相邻格子都不能是地雷
        if n == 0:
            for pos in neighbors:
                if pos is not None:  # 确保位置在棋盘内
                    ni, nj = pos
                    solver.add(Not(self.cells[ni][nj]))
            return
        
        # 创建变量表示相邻位置是否状态改变
        changes = [Bool(f"change_{i}_{j}_{k}") for k in range(8)]
        
        # 对于每对相邻位置（包括首尾相接）
        for k in range(8):
            next_k = (k + 1) % 8
            pos1 = neighbors[k]
            pos2 = neighbors[next_k]
            
            # 当前位置状态
            curr_is_mine = (False if pos1 is None 
                        else self.cells[pos1[0]][pos1[1]])
            # 下一个位置状态
            next_is_mine = (False if pos2 is None 
                        else self.cells[pos2[0]][pos2[1]])
            
            # 状态改变时changes[k]为True
            solver.add(changes[k] == Xor(curr_is_mine, next_is_mine))
        
        # 状态改变的次数除以2就是连续区域数
        solver.add(Sum([If(change, 1, 0) for change in changes]) 
                == 2 * n)
    
    def add_max_mine_group_constraints(self, solver, n, i, j):
        """添加最长连续雷长度的约束"""
        neighbors = self.get_ordered_neighbors(i, j)
        max_length = Int(f"max_len_{i}_{j}")
        lengths = []  # 存储每个起始位置的连续长度
        
        # 对于每个起始位置
        for start in range(8):
            length = Int(f"len_{i}_{j}_{start}")
            lengths.append(length)
            
            # 检查这个位置开始往后最多能有多少个连续的雷
            seq_positions = []  # 存储从start开始的连续位置
            for k in range(8):
                pos = neighbors[(start + k) % 8]
                if pos is None:  # 边界外就停止搜索
                    break
                seq_positions.append(pos)
            
            if seq_positions:  # 如果有有效位置
                # 从这个位置开始，计算最长的连续雷长度
                solver.add(length >= 0)
                solver.add(length <= len(seq_positions))
                
                # 对于每个可能的长度值
                for l in range(len(seq_positions) + 1):
                    conditions = []
                    # 如果长度是l，那么前l个位置必须是雷
                    if l > 0:
                        conditions.extend([self.cells[p[0]][p[1]] 
                                        for p in seq_positions[:l]])
                    # 且第l个位置（如果存在）必须不是雷
                    if l < len(seq_positions):
                        conditions.append(Not(self.cells[seq_positions[l][0]][seq_positions[l][1]]))
                    if conditions:
                        solver.add(Implies(length == l, And(conditions)))
            else:  # 如果这个起始位置就在边界外
                solver.add(length == 0)
        
        # 最大长度约束
        solver.add(max_length >= 0)
        solver.add(max_length == n)
        solver.add(And([max_length >= l for l in lengths]))
        solver.add(Or([max_length == l for l in lengths]))
    
    def add_strip_constraints(self, solver):
        """添加战舰约束（只能有1x1,1x2,1x3,1x4的雷区，且雷区互不接触（包括斜向））"""
        height, width = self.height, self.width
    
        #禁止斜向相邻
        for i in range(height):
            for j in range(width):
                # 右上
                if i > 0 and j < width-1:
                    solver.add(Not(And(self.cells[i][j], self.cells[i-1][j+1])))
                # 右下
                if i < height-1 and j < width-1:
                    solver.add(Not(And(self.cells[i][j], self.cells[i+1][j+1])))
        
        def get_ship_conditions(pos, length, is_horizontal):
            """获取特定长度战舰在特定位置的所有可能情况
            pos: 当前检查的位置(i,j)
            length: 战舰长度(2-4)
            is_horizontal: 是否是水平方向的战舰"""
            i, j = pos
            conditions = []
            size = width if is_horizontal else height
            
            # 遍历当前位置可能在战舰中的所有位置
            for start_offset in range(length):
                # 计算战舰的起始位置
                start_idx = (j if is_horizontal else i) - start_offset
                # 如果起始位置会导致战舰超出边界，跳过
                if start_idx < 0 or start_idx + length > size:
                    continue
                    
                # 收集构成战舰的所有格子
                ship_cells = []
                for k in range(length):
                    ship_pos = (i, start_idx + k) if is_horizontal else (start_idx + k, j)
                    ship_cells.append(self.cells[ship_pos[0]][ship_pos[1]])
                
                # 检查战舰前后是否有地雷
                checks = []
                if start_idx > 0:  # 检查前面一格
                    prev_pos = (i, start_idx - 1) if is_horizontal else (start_idx - 1, j)
                    checks.append(Not(self.cells[prev_pos[0]][prev_pos[1]]))
                if start_idx + length < size:  # 检查后面一格
                    next_pos = (i, start_idx + length) if is_horizontal else (start_idx + length, j)
                    checks.append(Not(self.cells[next_pos[0]][next_pos[1]]))
                
                # 组合所有条件
                condition = And(
                    *[cell for cell in ship_cells],  # 战舰格子都是地雷
                    *checks  # 前后没有地雷
                )
                conditions.append(condition)
                
            return conditions

        # 2. 战舰长度约束
        for i in range(height):
            for j in range(width):
                possible_shapes = []
                
                # 1x1战舰
                is_single = True
                if i > 0:
                    is_single = And(is_single, Not(self.cells[i-1][j]))
                if i < height-1:
                    is_single = And(is_single, Not(self.cells[i+1][j]))
                if j > 0:
                    is_single = And(is_single, Not(self.cells[i][j-1]))
                if j < width-1:
                    is_single = And(is_single, Not(self.cells[i][j+1]))
                possible_shapes.append(is_single)
                
                # 2-4格战舰
                for length in range(2, 5):
                    # 水平方向
                    possible_shapes.extend(get_ship_conditions((i, j), length, True))
                    # 垂直方向
                    possible_shapes.extend(get_ship_conditions((i, j), length, False))
                
                # 如果这个格子是地雷，它必须符合某一个合法形状
                solver.add(Implies(self.cells[i][j], Or(possible_shapes)))
    
    def add_mine_groups_size_constraints(self, solver, group_sizes, i, j):
        """添加连续雷区域大小的约束"""
        neighbors = self.get_ordered_neighbors(i, j)
        
        # 生成所有可能的模式
        patterns = generate_group_patterns(group_sizes, neighbors)
        
        # 为每个模式创建一个条件
        pattern_conditions = []
        for pattern in patterns:
            condition = []
            for k, (should_be_mine, pos) in enumerate(zip(pattern, neighbors)):
                if pos is not None:  # 只对棋盘内的格子添加约束
                    ni, nj = pos
                    if should_be_mine == "1":
                        condition.append(self.cells[ni][nj])
                    else:
                        condition.append(Not(self.cells[ni][nj]))
            if condition:  # 确保有约束才添加
                pattern_conditions.append(And(*condition))
        
        # 至少满足一种模式
        if pattern_conditions:  # 确保有条件才添加
            solver.add(Or(*pattern_conditions))
                        
    def find_next_determined_cell(self, board):
        """找出下一个可以确定状态的格子，优先考虑靠近线索的格子"""
        solver = self.create_basic_formula(board)
        
        # 获取所有未知格子和线索格子
        unknown_cells = []
        clue_cells = []
        for i in range(self.height):
            for j in range(self.width):
                if board[i][j] == -1:  # 未知格子
                    unknown_cells.append((i, j))
                elif isinstance(board[i][j], int) and board[i][j] >= 0 or isinstance(board[i][j], tuple):  # 数字线索格子（包括tuple格式）
                    clue_cells.append((i, j))
        
        # 为每个未知格子计算到最近线索的距离
        cell_distances = []
        for unknown in unknown_cells:
            min_distance = float('inf')
            for clue in clue_cells:
                dist = manhattan_distance(unknown, clue)
                min_distance = min(min_distance, dist)
            cell_distances.append((unknown, min_distance))
        
        # 按距离排序，优先检查距离近的格子
        cell_distances.sort(key=lambda x: x[1])
        
        # 按距离顺序检查每个未知格子
        for (i, j), _ in cell_distances:
            # 尝试假设是地雷
            s1 = Solver()
            s1.add(solver.assertions())
            s1.add(self.cells[i][j])
            mine_status = s1.check()
            
            # 尝试假设不是地雷
            s2 = Solver()
            s2.add(solver.assertions())
            s2.add(Not(self.cells[i][j]))
            safe_status = s2.check()
            
            # 根据结果判断格子状态
            if mine_status == sat and safe_status == unsat:
                print(f"发现确定的地雷位置: ({i},{j})")
                return (i, j, 1)  # 1表示地雷
            elif mine_status == unsat and safe_status == sat:
                print(f"发现确定的安全位置: ({i},{j})")
                return (i, j, 0)  # 0表示安全
            elif mine_status == unsat and safe_status == unsat:
                raise ValueError("出现矛盾！")
        
        return None  # 没有找到确定的格子

def find_groups(pattern):
    """找出模式中所有连续1的组的大小"""
    if not pattern:
        return []
    
    if '1' not in pattern:
        return [0]
    
    # 先按断开处理，找出所有组    
    groups = []
    count = 0
    for c in pattern:
        if c == '1':
            count += 1
        elif count > 0:
            groups.append(count)
            count = 0
    if count > 0:
        groups.append(count)
    
    # 如果首尾都是1，则将最后一组加到第一组
    if pattern[0] == '1' and pattern[-1] == '1' and len(groups) > 1:
        groups[0] += groups[-1]
        groups.pop()
        
    return groups

def generate_group_patterns(sizes, neighbors):
    """生成所有可能的合法模式"""
    total_mines = sum(sizes)
    pattern_length = 8
    valid_patterns = []
    
    def backtrack(curr_pattern, mines_left):
        if len(curr_pattern) == pattern_length:
            if mines_left == 0:
                groups = find_groups(curr_pattern)
                if sorted(groups) == sorted(sizes):
                    valid_patterns.append(curr_pattern)
            return
            
        # 当前位置不存在（棋盘外）或已经没有剩余的雷可放
        if neighbors[len(curr_pattern)] is None or mines_left == 0:
            backtrack(curr_pattern + "0", mines_left)
        elif mines_left > 0:  # 还有雷可以放
            backtrack(curr_pattern + "1", mines_left - 1)  # 放雷
            backtrack(curr_pattern + "0", mines_left)      # 不放雷
    
    backtrack("", total_mines)
    return valid_patterns

def solve_minesweeper(board, total_mines, rule_type=['V']):
    """输入当前棋盘状态和总地雷数，返回所有可以确定的格子"""
    height, width = len(board), len(board[0])
    solver = MinesweeperSATSolver(height, width, total_mines, rule_type)
    return solver.find_next_determined_cell(board)

if __name__ == "__main__":
    # from get_board import get_game_board
    
    # board = get_game_board()
    # print(board)

    board = [[-1, -3, -3, (6, ['L', 'M']), -2], [-2, (7, ['M', 'X']), -3, (5, ['E']), -3], [-1, -3, -2, (1, ['W\'']), (5, ['M', 'X'])], [(3, ['X']), -3, -1, -2, -3], [(5, ['E']), (2, ['V']), -1, (2, ['P']), -3]]
    print(solve_minesweeper(board, 10, ['#']))