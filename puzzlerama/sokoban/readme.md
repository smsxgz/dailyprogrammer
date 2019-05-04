A Sokoban solver in Python.

<center><img src="/images/out_001.png" alt="drawing" style="width:500px;"/></center>

The codes can be found in https://github.com/smsxgz/dailyprogrammer/tree/master/puzzlerama/sokoban.
<!--more-->

In following, we introduce some details in our implement of Sokoban solver.

### Normalized player position
Consider that two states is equivalent if the boxes are at the same positions and the player positions are in the same player access area, so we can only store normalized player position. We use positions of boxes and top-left reachable position as our state to reduce the number of states in the search tree.

### Deadlocks
We only consider the simple deadlocks from which a box never can be pushed to a goal, no matter where the other boxes are located in the board. Once we push a box into a square which is a deadlock, the state becomes unsolvable immediately.

We detect the simple deadlocks by searching all squares where we can __pull__ a box from one of the goals to. A simple breadth-first-searching is enough.

### A* search algorithm
We use a Fibonacci heap for the priority queue required in A* search algorithm. For each state, we store the information, including box positions, normalized player position, reachable position, available moves, f-score, g-score, in a node of the heap and employ a dictionary to record corresponding pointer to the corresponding node.

It worth noting that __standard__ binary heap, leftist heap and binomial heap are not qualified for the work here. In standard leftist heap or binomial heap, if we decrease value of a node, we may need to swap the value of some nodes instead of nodes themselves to fix the heap. Of course we can modify standard leftist heap or binomial heap to reach our needs, for example we can apply doubly linked list instead of singly linked list in standard binomial heap to make exchange nodes directly possible.

<br>
<center><img src="/images/sample.gif" alt="drawing" style="width:500px;"/></center>


### Reference
1. http://sokobano.de/wiki/index.php?title=Solver
2. http://sokobano.de/wiki/index.php?title=How_to_detect_deadlocks
3. https://blog.csdn.net/yzf0011/article/details/60574388 (Fibonacci heap)
4. https://github.com/natebrennand/Sokoban
5. https://en.wikipedia.org/wiki/A*_search_algorithm
