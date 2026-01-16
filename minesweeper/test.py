import unittest
from z3 import *
from solver_z3 import MinesweeperSATSolver

class TestMinesweeperConnectivity(unittest.TestCase):
    def setUp(self):
        
        self.test_board = [
            [-1, -1, -1, -1, -1],
            [-1, -1, -3, -1, -1],
            [1, 3, 3, -1, -1],
            [-1, 3, -3, 5, -1],
            [-1, 3, -1, -1, -1]
        ]
        self.ms = MinesweeperSATSolver(5, 5, 10, 'O')
        
    def print_board_info(self, model):
        print("\n=== 棋盘状态信息 ===")
        # 打印每个格子的状态
        print("\n地雷状态 (True表示有雷):")
        for i in range(5):
            row = []
            for j in range(5):
                is_mine = model.eval(self.ms.cells[i][j])
                row.append(str(is_mine))
            print(f"行 {i}: {row}")
            
        print("\n非雷格距离:")
        for i in range(5):
            row = []
            for j in range(5):
                dist = model.eval(Int(f"safe_dist_{i}_{j}")).as_long()
                row.append(f"{dist:2d}")
            print(f"行 {i}: {row}")
            
        print("\n雷格距离:")
        for i in range(5):
            row = []
            for j in range(5):
                dist = model.eval(Int(f"mine_dist_{i}_{j}")).as_long()
                row.append(f"{dist:2d}")
            print(f"行 {i}: {row}")
            
    def test_given_board(self):
        print("\n开始测试给定棋盘...")
        print("原始棋盘状态:")
        for row in self.test_board:
            print(row)
            
        self.solver = self.ms.create_basic_formula(self.test_board)
        
        # 已知雷格位置约束
        print("\n添加已知雷格约束...")
        self.solver.add(self.ms.cells[1][2] == True)  # -3位置
        self.solver.add(self.ms.cells[3][2] == True)  # -3位置
        
        # 验证解的存在性
        result = self.solver.check()
        print(f"\n求解结果: {result}")
        self.assertEqual(result, sat)
        
        if result == sat:
            model = self.solver.model()
            self.print_board_info(model)
            
            # 验证特定位置
            print("\n=== 验证特定位置 ===")
            # 验证数字1位置的safe_distance
            pos_1_dist = model.eval(Int("safe_dist_2_0")).as_long()
            print(f"数字1位置(2,0)的safe_distance: {pos_1_dist}")
            self.assertEqual(pos_1_dist, 0)
            
            # 验证两个已知雷格的mine_distance
            mine_dist_1 = model.eval(Int("mine_dist_1_2")).as_long()
            mine_dist_2 = model.eval(Int("mine_dist_3_2")).as_long()
            print(f"雷格(1,2)的mine_distance: {mine_dist_1}")
            print(f"雷格(3,2)的mine_distance: {mine_dist_2}")
            self.assertGreater(mine_dist_1, -1)
            self.assertGreater(mine_dist_2, -1)

if __name__ == '__main__':
    unittest.main(verbosity=2)