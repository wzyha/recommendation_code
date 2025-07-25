from graphviz import Digraph

# 创建一个有向图对象
dot = Digraph(comment='基于社群的推荐算法示意图')

# 添加节点和边
dot.node('A', '用户数据\n(购买记录、社交关系)')
dot.node('B', '构建用户网络')
dot.node('C', '应用Louvain算法\n划分社群')
dot.node('D', '确定当前用户\n所在社群')
dot.node('E', '统计社群内其他用户\n购买频率最高的产品')
dot.node('F', '为当前用户推荐\n购买频率最高的产品')

# 添加边
dot.edge('A', 'B', label='1. 数据预处理')
dot.edge('B', 'C', label='2. 社群划分')
dot.edge('C', 'D', label='3. 社群定位')
dot.edge('D', 'E', label='4. 购买行为分析')
dot.edge('E', 'F', label='5. 推荐生成')

# 设置图形样式
dot.attr(bgcolor='lightblue', label='基于社群的推荐算法流程', fontname='Arial', fontsize='14')

# 保存和显示图形
dot.render('community_based_recommendation', format='png', view=True)