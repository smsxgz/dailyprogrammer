"""
Improved Tumblestone Game Solver
A solver for the Tumblestone puzzle game that handles special blocks and rules,
including column switches that toggle after each block collection, hive mode,
and rolling rows that shift after each move.
"""

from typing import List, Tuple, Set, Optional, FrozenSet, Dict
from enum import Enum
from collections import deque, defaultdict
import copy
import time
import heapq
import win32api
import win32con
import win32gui
import time


class BlockType(Enum):
    RED = 'R'
    GREEN = 'G'
    YELLOW = 'Y'
    PURPLE = 'P'
    BLUE = 'B'
    BRICK = 'Z'  # Brick block
    WILDCARD = 'W'  # Wildcard block that can match any color
    EMPTY = '.'
    
    def __repr__(self):
        return self.value


class GameState:
    def __init__(self, board: List[List[BlockType]], column_switches: List[Optional[bool]] = None, 
                 prevent_same_color: bool = False, alternating_locks: bool = False,
                 rolling_rows: Dict[int, bool] = None, combo_mode: bool = False,
                 reverse_column_on_match: bool = False, invisible_top_after_first: bool = False,
                 rhythm_mode: bool = False):
        # Store board as a list of columns (not rows) for more efficient access
        self.columns = self._transpose_board(board)
        self.width = len(board)
        self.height = len(board[0]) if board else 0
        self.buffer = []  # Buffer for collected blocks
        # Column switch states: True=on (can collect), False=off (can't collect), None=no switch
        self.column_switches = column_switches if column_switches is not None else [None] * self.width
        # Track total moves for switch state determination
        self.total_moves = 0
        # Pre-calculate top blocks for each column
        self.top_blocks = self._calculate_top_blocks()
        # Store second-level blocks for invisible top mode
        self.second_level_blocks = self._calculate_second_level_blocks()
        # Track remaining blocks for quick solved check
        self.remaining_blocks = sum(sum(1 for block in col if block != BlockType.EMPTY) for col in self.columns)
        # Track last eliminated color
        self.last_eliminated_color = None
        # Whether to prevent consecutive eliminations of the same color
        self.prevent_same_color = prevent_same_color
        # Whether to use alternating locks mode
        self.alternating_locks = alternating_locks
        # Track if we're in the first lock state (True) or second lock state (False)
        self.is_first_lock_state = True
        # Track which rows should roll after a move (dict: row_index -> should_roll)
        self.rolling_rows = rolling_rows if rolling_rows is not None else {}
        # Combo mode flag
        self.combo_mode = combo_mode
        # Reverse column on match flag
        self.reverse_column_on_match = reverse_column_on_match
        # Invisible top layer after first block flag
        self.invisible_top_after_first = invisible_top_after_first
        # Flag to track if we're collecting the second block (after first, before third)
        self.collecting_second_block = False
        # Rhythm mode flag
        self.rhythm_mode = rhythm_mode
        # Cooldowns for rhythm mode (turn number when column becomes available again)
        self.column_cooldowns = [0] * self.width

    def _transpose_board(self, board: List[List[BlockType]]) -> List[List[BlockType]]:
        if not board:
            return []
        return [col[::-1] for col in board]
    
    def _calculate_top_blocks(self) -> List[Optional[Tuple[int, BlockType]]]:
        """Pre-calculate the top block (position and type) for each column"""
        result = []
        for col_idx, column in enumerate(self.columns):
            for pos, block in enumerate(column):
                if block != BlockType.EMPTY:
                    result.append((pos, block))
                    break
            else:
                result.append(None)  # No blocks in this column
        return result
    
    def _calculate_second_level_blocks(self) -> List[Optional[Tuple[int, BlockType]]]:
        """Pre-calculate the second level block (position and type) for each column"""
        result = []
        for col_idx, column in enumerate(self.columns):
            first_non_empty = None
            second_non_empty = None
            for pos, block in enumerate(column):
                if block != BlockType.EMPTY:
                    if first_non_empty is None:
                        first_non_empty = pos
                    else:
                        second_non_empty = (pos, block)
                        break
            result.append(second_non_empty)  # Might be None if column has 0 or 1 blocks
        return result

    def is_block_locked(self, col: int, row: int) -> bool:
        """Check if a block at the given position is locked based on alternating locks mode"""
        if not self.alternating_locks:
            return False
        
        # Calculate if the position should be locked in the current state
        position_parity = (col + row) % 2
        height_parity = self.height % 2
        
        # In first lock state, lock positions where (col + row) has same parity as height
        # In second lock state, lock positions where (col + row) has different parity from height
        should_be_locked = (position_parity == height_parity) == self.is_first_lock_state
        
        return should_be_locked

    def is_valid_move(self, col: int) -> bool:
        """Check if a block can be collected from the specified column"""
        if col < 0 or col >= self.width:
            return False
        
        # 检查列开关状态
        if self.column_switches[col] is not None and not self.column_switches[col]:
            return False
            
        # 检查节奏模式冷却
        if self.rhythm_mode and self.total_moves < self.column_cooldowns[col]:
            return False
        
        # 确定要检查的方块
        target_block_info = None
        if self.invisible_top_after_first and self.collecting_second_block:
            target_block_info = self.second_level_blocks[col]
        else:
            target_block_info = self.top_blocks[col]
            
        if target_block_info is None:
            return False  # 该列没有可收集的方块
            
        pos, block = target_block_info
        
        # 如果目标方块是砖块，不能收集
        if block == BlockType.BRICK:
            return False
            
        # 检查交替锁定模式中方块是否被锁定
        if self.alternating_locks and self.is_block_locked(col, pos):
            return False
        
        # 如果启用了防止相同颜色模式，且当前方块与上次消除的颜色相同，则不允许收集
        if self.prevent_same_color and self.last_eliminated_color is not None:
            # 只要方块不是通配符且与上次消除的颜色相同，就不允许收集
            if block != BlockType.WILDCARD and block == self.last_eliminated_color:
                return False
        
        # 如果缓冲区为空，任何非砖块方块都有效
        if not self.buffer:
            return True
            
        # 缓冲区不为空，检查兼容性
        buffer_len = len(self.buffer)
        last_buffer = self.buffer[-1]
        compatible = False

        # 特殊通配符情况：WX + Y -> 必须匹配X（如果X不是W）
        if buffer_len == 2 and self.buffer[1] == BlockType.WILDCARD and self.buffer[0] != BlockType.WILDCARD:
            if block == self.buffer[0] or block == BlockType.WILDCARD:
                compatible = True
        # 一般情况：方块必须与缓冲区最后一个匹配，或者其中一个必须是通配符
        elif block == last_buffer or block == BlockType.WILDCARD or last_buffer == BlockType.WILDCARD:
            compatible = True

        if not compatible:
            return False
        
        # 所有检查通过
        return True

    def is_valid_combo_move(self, col: int) -> bool:
        """Check if a move is valid in combo mode (requires two consecutive valid moves)."""
        # First move must be valid normally
        if not self.is_valid_move(col):
            return False
        
        # Simulate the first move
        temp_state = self.copy()
        # Use internal flag to prevent recursive combo check in make_move during simulation
        if not temp_state._perform_single_move(col):
            # Should not happen if is_valid_move passed, but defensive check
            return False 

        # Check second move validity
        if temp_state.invisible_top_after_first and temp_state.collecting_second_block:
            top_info = temp_state.second_level_blocks[col]
        else:
            top_info = temp_state.top_blocks[col]

        # Special case: If column is empty, has a brick, or the target block is locked after the first move, combo is allowed
        is_second_move_blocked = False
        if top_info is None:
            is_second_move_blocked = True
        elif top_info[1] == BlockType.BRICK:
            is_second_move_blocked = True
        elif temp_state.alternating_locks and temp_state.is_block_locked(col, top_info[0]):
            is_second_move_blocked = True
        elif temp_state.column_switches[col] is False:
            is_second_move_blocked = True
        elif temp_state.prevent_same_color and top_info[1] == temp_state.last_eliminated_color:
            is_second_move_blocked = True
        if is_second_move_blocked:
            return True
        
        # Otherwise, the second move must also be valid according to standard rules
        return temp_state.is_valid_move(col)

    def get_valid_moves(self) -> List[int]:
        """Get all valid columns for collection, considering combo mode."""
        if self.combo_mode:
            return [col for col in range(self.width) if self.is_valid_combo_move(col)]
        else:
            return [col for col in range(self.width) if self.is_valid_move(col)]

    def get_state_hash(self) -> str:
        """Generate a hash for the current state for efficient comparison"""
        # Flatten the board representation
        board_state = ''.join(''.join(block.value for block in col) for col in self.columns)
        # Add buffer and switch states to create unique hash
        buffer_state = ''.join(block.value for block in self.buffer)
        switch_state = ''.join('1' if switch else '0' if switch is False else 'N' for switch in self.column_switches)
        # Add last eliminated color to the hash
        last_color = self.last_eliminated_color.value if self.last_eliminated_color else 'N'
        # Add alternating locks state to the hash
        lock_state = '1' if self.is_first_lock_state else '0' if self.alternating_locks else 'N'
        # Add rolling rows state to the hash
        rolling_state = ','.join(f"{row}:{1 if roll else 0}" for row, roll in sorted(self.rolling_rows.items()))
        # Add invisible top state
        invisible_state = '1' if self.invisible_top_after_first and self.collecting_second_block else '0'
        # Add rhythm mode cooldown state
        rhythm_state = ''.join(str(cd) for cd in self.column_cooldowns) if self.rhythm_mode else ''
        # Add total moves (relevant for rhythm mode)
        moves_state = str(self.total_moves) if self.rhythm_mode else ''
        
        return f"{board_state}|{buffer_state}|{switch_state}|{last_color}|{lock_state}|{rolling_state}|{invisible_state}|{rhythm_state}|{moves_state}"
    
    def estimate_distance_to_goal(self) -> int:
        """Heuristic function for A* search - estimates moves needed to solve"""
        # Count remaining blocks and consider buffer state
        return self.remaining_blocks + len(self.buffer) // 3

    def get_display_board(self) -> List[List[BlockType]]:
        """Convert internal column-based representation to row-based for display"""
        board = [[BlockType.EMPTY for _ in range(self.width)] for _ in range(self.height)]
        for col_idx, column in enumerate(self.columns):
            for row_idx, block in enumerate(column):
                board[row_idx][col_idx] = block
        return board

    def __str__(self) -> str:
        """String representation of the game state"""
        board = self.get_display_board()
        result = []
        for row_idx, row in enumerate(board):
            row_str = ''.join(block.value for block in row)
            if row_idx in self.rolling_rows and self.rolling_rows[row_idx]:
                row_str += f" (Rolling row {row_idx})"
            result.append(row_str)
        result.append(f"Buffer: {''.join(block.value for block in self.buffer)}")
        result.append(f"Switches: {['ON' if s else 'OFF' if s is False else 'None' for s in self.column_switches]}")
        result.append(f"Total moves: {self.total_moves}")
        result.append(f"Remaining blocks: {self.remaining_blocks}")
        rolling_rows_str = ", ".join(f"Row {row}" for row, is_rolling in self.rolling_rows.items() if is_rolling)
        if rolling_rows_str:
            result.append(f"Rolling rows: {rolling_rows_str}")
        if self.alternating_locks:
            result.append(f"Alternating locks: {'First state' if self.is_first_lock_state else 'Second state'}")
        if self.reverse_column_on_match:
            result.append("Reverse column on match: Enabled")
        if self.prevent_same_color:
            result.append("Prevent same color: Enabled")
        if self.combo_mode:
            result.append("Combo mode: Enabled")
        if self.invisible_top_after_first:
            result.append("Invisible top after first: Enabled")
            if self.collecting_second_block:
                result.append("Currently collecting second block (top layer invisible)")
        if self.rhythm_mode:
            result.append("Rhythm mode: Enabled")
            cooldown_strs = []
            for i, cd in enumerate(self.column_cooldowns):
                if cd > self.total_moves:
                    cooldown_strs.append(f"Col {i} available in {cd - self.total_moves} moves (turn {cd})")
            if cooldown_strs:
                result.append(f"Cooldowns: {'; '.join(cooldown_strs)}")
            else:
                result.append("Cooldowns: All columns available")
        
        return '\n'.join(result)

    def copy(self) -> 'GameState':
        """Create a deep copy of the game state"""
        new_state = GameState([], self.column_switches.copy(), self.prevent_same_color, 
                              self.alternating_locks, self.rolling_rows.copy(), self.combo_mode,
                              self.reverse_column_on_match, self.invisible_top_after_first,
                              self.rhythm_mode)
        new_state.columns = [col[:] for col in self.columns]
        new_state.height = self.height
        new_state.width = self.width
        new_state.buffer = self.buffer[:]
        new_state.total_moves = self.total_moves
        new_state.top_blocks = self.top_blocks[:]
        new_state.second_level_blocks = self.second_level_blocks[:]
        new_state.remaining_blocks = self.remaining_blocks
        new_state.last_eliminated_color = self.last_eliminated_color
        new_state.is_first_lock_state = self.is_first_lock_state
        new_state.rolling_rows = self.rolling_rows.copy() if self.rolling_rows else {}
        new_state.combo_mode = self.combo_mode
        new_state.collecting_second_block = self.collecting_second_block
        new_state.rhythm_mode = self.rhythm_mode
        new_state.column_cooldowns = self.column_cooldowns[:]
        return new_state

    def _perform_rolling(self):
        """Roll blocks in designated rolling rows"""
        for row_idx, should_roll in self.rolling_rows.items():
            if should_roll and 0 <= row_idx < self.height:
                # Gather blocks from this row across all columns
                row_blocks = []
                for col_idx in range(self.width):
                    if row_idx < len(self.columns[col_idx]):
                        row_blocks.append(self.columns[col_idx][row_idx])
                    else:
                        row_blocks.append(BlockType.EMPTY)
                
                # Roll the blocks one position to the right (circular)
                row_blocks = [row_blocks[-1]] + row_blocks[:-1]
                
                # Update the columns with the new block positions
                for col_idx in range(self.width):
                    if row_idx < len(self.columns[col_idx]):
                        self.columns[col_idx][row_idx] = row_blocks[col_idx]
        
        # Re-calculate top blocks after rolling
        self.top_blocks = self._calculate_top_blocks()
        self.second_level_blocks = self._calculate_second_level_blocks()

    def make_move(self, col: int) -> bool:
        """Collect a block (or two in combo mode) from the specified column."""
        if self.combo_mode:
            # Combo mode validity is checked by get_valid_moves calling is_valid_combo_move
            if not self.is_valid_combo_move(col):
                return False # Should not happen if called after get_valid_moves, but check

            # Perform the first move
            if not self._perform_single_move(col):
                return False # Should not happen
            
            # Check if second move is possible (column not empty, not a brick)
            top_info = self.top_blocks[col]
            if top_info is not None and top_info[1] != BlockType.BRICK:
                # Perform the second move only if possible
                if not self._perform_single_move(col):
                    # This might happen if the state changed unexpectedly (e.g., rolling rows affected validity)
                    # Or if the second part of the combo move is invalid for other reasons
                    # How to handle this? For now, let's assume it succeeds if the check passed.
                    # We might need to revert the first move if the second fails unexpectedly.
                    # For simplicity now, assume _perform_single_move succeeds if top is not None/Brick
                    pass
            return True
        else:
            # Standard mode: perform a single move
            if not self.is_valid_move(col):
                return False
            return self._perform_single_move(col)

    def _perform_single_move(self, col: int) -> bool:
        """Performs a single block collection and updates the state. Returns True if successful."""
        # --- Re-check validity START --- 
        # Check basic bounds and switch state AT THE MOMENT OF EXECUTION
        if not (0 <= col < self.width and self.column_switches[col] is not False):
            return False

        # Determine which block to use based on invisible top mode
        if self.invisible_top_after_first and self.collecting_second_block:
            top_info = self.second_level_blocks[col]
        else:
            top_info = self.top_blocks[col]
            
        if top_info is None:
            return False # Column empty or no second level block
            
        pos, block = top_info
        
        # Check for Brick or Lock
        if block == BlockType.BRICK or (self.alternating_locks and self.is_block_locked(col, pos)):
            return False 

        # Check buffer compatibility
        if self.buffer:
            buffer_len = len(self.buffer)
            last_buffer = self.buffer[-1]
            # Specific wildcard case
            if buffer_len == 2 and self.buffer[1] == BlockType.WILDCARD and self.buffer[0] != BlockType.WILDCARD:
                if not (block == self.buffer[0]): return False
            # General case: Block must match last in buffer, or one must be wildcard
            elif not (block == last_buffer or block == BlockType.WILDCARD or last_buffer == BlockType.WILDCARD):
                return False
        # --- Re-check validity END ---

        # Collect the block (Validity checks passed)
        self.buffer.append(block)
        
        # Handle invisible top mode collection
        if self.invisible_top_after_first and self.collecting_second_block:
            # In invisible top mode, collect second level block
            self.columns[col][pos] = BlockType.EMPTY
            
            # After collecting second block, top block drops down to fill the gap
            if self.top_blocks[col] is not None:
                top_pos, top_block = self.top_blocks[col]
                # Move top block down to the position of the collected second block
                self.columns[col][pos] = top_block
                self.columns[col][top_pos] = BlockType.EMPTY
            
            # Now recalculate top and second level blocks for this column
            self.top_blocks[col] = None
            self.second_level_blocks[col] = None
            
            # First find new top block
            for i in range(len(self.columns[col])):
                if self.columns[col][i] != BlockType.EMPTY:
                    self.top_blocks[col] = (i, self.columns[col][i])
                    # Then find second level block
                    for j in range(i + 1, len(self.columns[col])):
                        if self.columns[col][j] != BlockType.EMPTY:
                            self.second_level_blocks[col] = (j, self.columns[col][j])
                            break
                    break
                    
            # Turn off invisible top mode after collecting second block
            self.collecting_second_block = False
        else:
            # Normal collection (not invisible top mode or not collecting second block)
            self.columns[col][pos] = BlockType.EMPTY
            
            # Update top block for this column
            self.top_blocks[col] = None
            self.second_level_blocks[col] = None
            
            # Find new top and second level blocks
            first_non_empty = None
            for i in range(len(self.columns[col])):
                if self.columns[col][i] != BlockType.EMPTY:
                    if first_non_empty is None:
                        first_non_empty = i
                        self.top_blocks[col] = (i, self.columns[col][i])
                    else:
                        self.second_level_blocks[col] = (i, self.columns[col][i])
                        break
            
            # If this is the first block collected and invisible top mode is enabled
            if len(self.buffer) == 1 and self.invisible_top_after_first:
                self.collecting_second_block = True
        
        self.remaining_blocks -= 1
        
        # Update total moves and switch states
        self.total_moves += 1
        self._update_switches()
        
        # Update cooldown if rhythm mode is enabled
        if self.rhythm_mode:
            self.column_cooldowns[col] = self.total_moves + 3

        # Toggle lock state if in alternating locks mode
        if self.alternating_locks:
            self.is_first_lock_state = not self.is_first_lock_state

        # Perform rolling after each move
        self._perform_rolling() # Rolling happens *after* the move

        # Track if a match was made for reverse column functionality
        match_made = False
        # Clear buffer if possible
        if len(self.buffer) >= 3:
            last_three = self.buffer[-3:]
            is_match = False
            eliminated_color = None
            
            # Check for match considering wildcards
            non_wild = [b for b in last_three if b != BlockType.WILDCARD]
            if len(non_wild) == 0: # Three wildcards
                is_match = True
                eliminated_color = BlockType.WILDCARD # Or handle as needed
            elif len(non_wild) == 1: # Two wildcards, one color
                is_match = True
                eliminated_color = non_wild[0]
            elif len(non_wild) == 2: # One wildcard, two potential colors
                if non_wild[0] == non_wild[1]:
                    is_match = True
                    eliminated_color = non_wild[0]
            elif len(non_wild) == 3: # No wildcards
                if len(set(non_wild)) == 1:
                    is_match = True
                    eliminated_color = non_wild[0]

            if is_match:
                # Update last eliminated color and clear buffer
                self.last_eliminated_color = eliminated_color
                self.buffer = self.buffer[:-3]
                match_made = True
                
                # Reverse column if enabled and match occurred
                if self.reverse_column_on_match:
                    # --- Alt Reversal: Reverse between lowest and highest non-empty blocks ---                    
                    # Find the index of the lowest non-empty block
                    bottom_block_index = -1
                    for i in range(len(self.columns[col])): # Scan bottom-up
                        if self.columns[col][i] != BlockType.EMPTY:
                            bottom_block_index = i
                            break 
                    
                    # Find the index of the highest non-empty block
                    top_block_index = -1
                    for i in range(len(self.columns[col]) - 1, -1, -1): # Scan top-down
                        if self.columns[col][i] != BlockType.EMPTY:
                            top_block_index = i
                            break
                    
                    # If the column has blocks and bottom <= top, perform the reversal
                    if bottom_block_index != -1 and top_block_index != -1 and bottom_block_index <= top_block_index:
                        # Extract the segment between lowest and highest blocks (inclusive)
                        segment_to_reverse = self.columns[col][bottom_block_index : top_block_index + 1]
                        # Reverse this segment
                        segment_to_reverse.reverse()
                        # Place the reversed segment back into the column
                        idx = 0
                        for i in range(bottom_block_index, top_block_index + 1):
                           self.columns[col][i] = segment_to_reverse[idx]
                           idx += 1
                    # --- End Alt Reversal Logic ---
                    
                    # We need to recalculate top blocks (for all columns, safest after reversal)
                    self.top_blocks = self._calculate_top_blocks()
                    self.second_level_blocks = self._calculate_second_level_blocks()

        # Handle bricks (should be done after potential buffer clears)
        self._handle_bricks()
        return True # Indicate successful move

    def _update_switches(self):
        """Update all column switch states"""
        for col in range(self.width):
            if self.column_switches[col] is not None:
                # Toggle switch state after each move
                self.column_switches[col] = not self.column_switches[col]

    def _handle_bricks(self):
        """Handle bricks that can be cleared"""
        # Create a map of bricks by row for efficient processing
        bricks_by_row = defaultdict(list)
        for col_idx, column in enumerate(self.columns):
            for row_idx, block in enumerate(column):
                if block == BlockType.BRICK:
                    bricks_by_row[row_idx].append((col_idx, row_idx))
        
        if not bricks_by_row:
            return  # No bricks to process
        
        # Process each row with bricks
        changed = True
        while changed:
            changed = False
            for row, brick_positions in list(bricks_by_row.items()):
                # Check if this row contains only bricks and empty spaces
                row_empty = True
                for col in range(self.width):
                    block_type = self.columns[col][row] if row < len(self.columns[col]) else BlockType.EMPTY
                    if block_type != BlockType.EMPTY and block_type != BlockType.BRICK:
                        row_empty = False
                        break
                
                if row_empty and brick_positions:
                    # Clear all bricks in this row
                    for col_idx, row_idx in brick_positions:
                        self.columns[col_idx][row_idx] = BlockType.EMPTY
                        self.remaining_blocks -= 1
                        # Update top block if needed
                        if self.top_blocks[col_idx] and self.top_blocks[col_idx][0] == row_idx:
                            self.top_blocks[col_idx] = None
                            for i in range(row_idx + 1, self.height):
                                if self.columns[col_idx][i] != BlockType.EMPTY:
                                    self.top_blocks[col_idx] = (i, self.columns[col_idx][i])
                                    break
                    
                    # Remove processed bricks
                    del bricks_by_row[row]
                    changed = True

    def is_solved(self) -> bool:
        """Check if the game is solved"""
        return self.remaining_blocks == 0 and not self.buffer


def solve_game_dfs(initial_state: GameState) -> Optional[List[int]]:
    """
    Solve the game using DFS algorithm
    Returns a sequence of moves (column indices) or None (if unsolvable)
    """
    start_time = time.time()
    stack = [(initial_state, [])]
    seen = {initial_state.get_state_hash()}
    nodes_explored = 0
    max_stack_size = 1
    
    # Increased node limit slightly
    max_nodes = 2000000 

    while stack and nodes_explored < max_nodes:
        max_stack_size = max(max_stack_size, len(stack))
        current_state, moves = stack.pop()  # Pop from the end (LIFO)
        nodes_explored += 1
        
        if nodes_explored % 10000 == 0:
            print(f"Explored {nodes_explored} nodes, stack size: {len(stack)}")
        
        if current_state.is_solved():
            elapsed_time = time.time() - start_time
            print(f"Solution found in {elapsed_time:.2f} seconds!")
            print(f"Explored {nodes_explored} nodes")
            print(f"Maximum stack size: {max_stack_size}")
            return moves

        # Consider all valid moves from current state
        # Sort in reverse order to prioritize rightmost columns first
        valid_moves = sorted(current_state.get_valid_moves(), reverse=True)
        for col in valid_moves:
            new_state = current_state.copy()
            if new_state.make_move(col):
                state_hash = new_state.get_state_hash()
                if state_hash not in seen:
                    seen.add(state_hash)
                    new_moves = moves + [col, col] if new_state.combo_mode else moves + [col]
                    stack.append((new_state, new_moves))

    print(f"No solution found after exploring {nodes_explored} nodes")
    return None


def parse_board(board_str: str, switches_str: str = None, prevent_same_color: bool = False, 
                 alternating_locks: bool = False, rolling_rows_str: str = None, 
                 combo_mode: bool = False, reverse_column_on_match: bool = False, invisible_top_after_first: bool = False,
                 rhythm_mode: bool = False) -> GameState:
    """Parse game board, switch states, rolling rows, and combo mode from strings"""
    lines = [line.strip() for line in board_str.strip().split('\n') if line.strip()]
    
    # Find the maximum line length
    max_length = max(len(line) for line in lines)
    
    # Process each line, filling in empty cells
    board = []
    for line in lines:
        row = []
        for char in line.strip():
            if char == 'R':
                row.append(BlockType.RED)
            elif char == 'G':
                row.append(BlockType.GREEN)
            elif char == 'Y':
                row.append(BlockType.YELLOW)
            elif char == 'P':
                row.append(BlockType.PURPLE)
            elif char == 'B':
                row.append(BlockType.BLUE)
            elif char == 'Z':
                row.append(BlockType.BRICK)
            elif char == 'W':
                row.append(BlockType.WILDCARD)
            else:
                row.append(BlockType.EMPTY)
        # Fill to maximum length with empty cells
        while len(row) < max_length:
            row.append(BlockType.EMPTY)
        board.append(row)
    
    # Parse switch states
    column_switches = None
    if switches_str:
        column_switches = []
        for char in switches_str.strip():
            if char == '1':
                column_switches.append(True)
            elif char == '0':
                column_switches.append(False)
            elif char == '.':
                column_switches.append(None)
            else:
                column_switches.append(None)
    
    # Parse rolling rows (comma-separated list of row numbers to roll)
    rolling_rows = {}
    if rolling_rows_str:
        try:
            row_indices = [int(idx.strip()) for idx in rolling_rows_str.split(',') if idx.strip()]
            for row_idx in row_indices:
                # Need to adjust row index based on internal representation (bottom is 0)
                # Assuming input is 1-based from top, and height is len(board[0]) ?
                # Let's assume the board is already parsed
                if board:
                    height = len(board[0])
                    internal_row_idx = height - row_idx # Adjust if input is 1-based from top
                    if 0 <= internal_row_idx < height:
                         rolling_rows[internal_row_idx] = True
                    else:
                        print(f"Warning: Invalid row index {row_idx} for rolling row.")
                else:
                    print("Warning: Cannot parse rolling rows for empty board.")
        except ValueError:
            print(f"Warning: Invalid rolling rows format '{rolling_rows_str}'. Expected comma-separated list of integers.")
    
    return GameState(board, column_switches, prevent_same_color, alternating_locks, rolling_rows, combo_mode, reverse_column_on_match, invisible_top_after_first, rhythm_mode)


def play_solution(moves: List[int], initial_position: int = 2):
    """
    Automatically play the game using the solution moves.
    Args:
        moves: List of column indices to collect from
        initial_position: Initial position of the character (0-4)
    """
    # Click the game window to ensure it's active
    hwnd = win32gui.FindWindow(None, "Tumblestone")
    if hwnd == 0:
        raise Exception('找不到Tumblestone窗口')
    
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    
    rect = win32gui.GetWindowRect(hwnd)
    # Click on the left side of the window
    click_x = rect[0] + 50  # 50 pixels from the left edge
    click_y = rect[1] + 100  # 100 pixels from the top edge
    win32api.SetCursorPos((click_x, click_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, click_x, click_y, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, click_x, click_y, 0, 0)
    time.sleep(0.5)  # Wait a bit after clicking
    
    current_pos = initial_position
    
    # The moves list now contains individual actions, even in combo mode (e.g., [1, 1, 3, 3])
    # So, just iterate and perform each action.
    for move_index, target_col in enumerate(moves):
        # Move to the target column
        while current_pos < target_col:
            win32api.keybd_event(win32con.VK_RIGHT, 0, 0, 0)  # Press right
            time.sleep(0.05)  # Small delay for movement
            win32api.keybd_event(win32con.VK_RIGHT, 0, win32con.KEYEVENTF_KEYUP, 0)  # Release right
            current_pos += 1
            time.sleep(0.05)  # Small delay between moves
            
        while current_pos > target_col:
            win32api.keybd_event(win32con.VK_LEFT, 0, 0, 0)  # Press left
            time.sleep(0.05)  # Small delay for movement
            win32api.keybd_event(win32con.VK_LEFT, 0, win32con.KEYEVENTF_KEYUP, 0)  # Release left
            current_pos -= 1
            time.sleep(0.05)  # Small delay between moves
        
        # Collect the block
        win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)  # Press space
        time.sleep(0.1)  # Small delay for collection
        win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)  # Release space
        time.sleep(0.1)  # Wait for animation


def simulate_game(initial_state: GameState, moves: List[int]):
    """Simulates the game step by step using a given move sequence for debugging."""
    print("\n--- Starting Simulation ---")
    current_state = initial_state.copy()
    
    print("Initial State (Move 0):")
    print(current_state)
    print("-------------------------")

    move_num = 0
    actual_moves_performed = 0 # Track moves considering combo

    # If combo mode, moves list contains pairs [c, c, c', c', ...]
    # If not combo mode, moves list is [c, c', c'', ...]
    step = 2 if initial_state.combo_mode else 1
    
    for i in range(0, len(moves), step):
        move_num += 1
        col = moves[i] # The column to interact with
        
        print(f"Attempting Move {move_num} (Column {col}):")
        
        # Make a copy *before* the move to show the state if it fails
        state_before_move = current_state.copy()
        
        success = current_state.make_move(col)
        
        if success:
            actual_moves_performed += step
            print(f"Move {move_num} Successful. State after move:")
            print(current_state)
            print("-------------------------")
            # Check if solved after this move
            if current_state.is_solved():
                print("--- Game Solved! ---")
                break
            # Wait for user input before next move
            input("Press Enter to continue to the next step...") 
        else:
            print(f"***** MOVE {move_num} (Column {col}) FAILED! *****")
            print("State before failed move attempt:")
            print(state_before_move) # Show the state before the failed attempt
            print("Reason: Move deemed invalid by make_move execution.")
            print("-------------------------")
            # Wait for user input even on failure
            input("Press Enter to continue simulation...")
            # Optionally break simulation on failure
            # break
            
    print(f"--- Simulation Complete --- ({actual_moves_performed} actual moves performed)")


def main(board_str: str, switches_str: str, prevent_same_color: bool = False, 
           alternating_locks: bool = False, rolling_rows_str: str = None,
           combo_mode: bool = False, reverse_column_on_match: bool = False, invisible_top_after_first: bool = False,
           rhythm_mode: bool = False):
    # Create initial state
    initial_state = parse_board(board_str, switches_str, prevent_same_color, alternating_locks, rolling_rows_str, combo_mode, reverse_column_on_match, invisible_top_after_first, rhythm_mode)
    print("Initial game state:")
    print(initial_state)     

    print("\nTrying DFS algorithm...")
    start_time = time.time()
    solution = solve_game_dfs(initial_state)
        
    if solution:
        elapsed_time = time.time() - start_time
        print(f"Time taken: {elapsed_time:.3f} seconds")
        print("Solution found with DFS!")
        print("Move sequence:")
        print(f"  {solution}")
        print(f"Total moves in sequence: {len(solution)}")
        
        # # --- Simulate the game --- 
        # simulate_game(initial_state, solution)
        # # -------------------------

        # Optional: Keep auto-play for actual gameplay
        # print("\nStarting auto-play in 3 seconds...")
        # time.sleep(1)  # Give user time to switch to game window
        gameplay_solution = solution[::2] if combo_mode else solution # Adjust for combo in gameplay
        play_solution(gameplay_solution)
    else:
        print("\nNo solution found")


if __name__ == '__main__':
    from get_board import get_board

    board_str = get_board()
    print(board_str)
  
#     board_str = """
# GGYRPYYPGRR
# RYGYYYGYYR.
# GYPPYRYR...
# GGYRPPYYGGR
# GPPPGRRR...
#     """
  
    switches_str = "....."  
    prevent_same_color = False
    alternating_locks = False
    rolling_rows_str = ""  # Example: rows 1 and 2 will roll
    combo_mode = False # Set combo mode
    reverse_column_on_match = False # 启用消除时列颠倒功能
    invisible_top_after_first = False # 启用收集第一个方块后顶层隐形功能
    rhythm_mode = False # Set rhythm mode
    
    main(board_str, switches_str, prevent_same_color, alternating_locks, rolling_rows_str, combo_mode, reverse_column_on_match, invisible_top_after_first, rhythm_mode)