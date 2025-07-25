import pandas as pd
import networkx as nx
from collections import defaultdict
import community as community_louvain  # 使用Louvain算法划分社区

# 创建一个无向图
G = nx.Graph()

# 使用字典记录每个顾客购买的产品列表
customer_products = defaultdict(list)

# 读取shopcart.xlsx文件
shopcart_file_path = "shopcart.xlsx"  # 替换为你的文件路径
df_shopcart = pd.read_excel(shopcart_file_path)

# 统计每个产品被哪些顾客购买
product_to_customers = defaultdict(set)
for _, row in df_shopcart.iterrows():
    customer_id = row['CUSTOMER_ID']
    product_id = row['PRODUCT_ID']
    product_to_customers[product_id].add(customer_id)

# 添加节点和边
for customers in product_to_customers.values():
    if len(customers) > 1:
        customer_list = list(customers)
        for i in range(len(customer_list)):
            for j in range(i + 1, len(customer_list)):
                customer1 = customer_list[i]
                customer2 = customer_list[j]
                if G.has_edge(customer1, customer2):
                    G[customer1][customer2]['weight'] += 1
                else:
                    G.add_edge(customer1, customer2, weight=1)

# 提取最大连通分量
largest_cc = max(nx.connected_components(G), key=len)
largest_subgraph = G.subgraph(largest_cc)

# 使用Louvain算法划分社区
partition = community_louvain.best_partition(largest_subgraph)

# 统计社区数量和每个社区的节点数量
community_count = defaultdict(int)
for community_id in partition.values():
    community_count[community_id] += 1

# 输出社区数量和每个社区的节点数量
print(f"总社区数量: {len(community_count)}")
for community_id, node_count in community_count.items():
    print(f"社区 {community_id} 包含 {node_count} 个节点")

# 将其中一个社区的所有节点输出到新的Excel表格文件
# 选择一个社区，例如社区0
selected_community_id = 2
selected_community_nodes = [node for node, community_id in partition.items() if community_id == selected_community_id]

# 创建一个DataFrame
df_community = pd.DataFrame(selected_community_nodes, columns=['Node'])

# 将DataFrame保存到Excel文件
output_file_path = "community2.xlsx"  # 输出文件路径
df_community.to_excel(output_file_path, index=False)

print(f"社区 {selected_community_id} 的所有节点已保存到文件 {output_file_path}")

# # 绘制最大连通分量的社区结构
# plt.figure(figsize=(12, 12))
# pos = nx.spring_layout(largest_subgraph, seed=42)  # 使用Spring布局
#
# # 绘制节点和边
# nx.draw_networkx_nodes(largest_subgraph, pos, node_size=50, node_color=list(partition.values()), cmap='viridis')
# nx.draw_networkx_edges(largest_subgraph, pos, alpha=0.5)
#
# # 添加节点标签（社区ID）
# node_labels = {node: f"{node} ({community_id})" for node, community_id in partition.items()}
# nx.draw_networkx_labels(largest_subgraph, pos, labels=node_labels, font_size=10, font_color='red')
#
# plt.title("Largest Connected Component with Community Structure")
# plt.show()