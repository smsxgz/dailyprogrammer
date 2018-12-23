v1: 利用'deepcopy'进行回溯  
v2: 手动复原状态进行回溯  
v3: 确认每个已完成路径经过了对应形状的所有普通顶点  
v4: 另一种处理边冲突的方式，并没有什么改进，见[denilsonsa/lyne-solver](https://github.com/denilsonsa/lyne-solver/blob/master/algorithm.js)  
v5: 确认当前顶点的可能边数不小于目标边数  
v6: 如果有邻居节点可能的边数小于目标边数，直接返回False；有过当前节点的目标边数还剩1，同时某个邻居节点可能边数和目标边数相等，那么下一步必须是这个邻居节点


利用v6可以完成所有关卡，每个耗时都不超过10分钟（我估计的）。
至此工程结束。  
![achievements](/LYNE/achievements.png)
