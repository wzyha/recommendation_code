import pandas as pd
import networkx as nx
from collections import defaultdict
import random
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

# 从 customer_network_analysis_20180601(1).xlsx 中读取数据
excel_file = pd.ExcelFile('customer_network_analysis_20180601(1).xlsx')
df_customer = excel_file.parse('Sheet1')

# 从 shopcart.xlsx 中加载数据
df_shopcart = pd.read_excel('shopcart.xlsx')
# 确保 PAY_DATE 列是日期时间格式
df_shopcart['PAY_DATE'] = pd.to_datetime(df_shopcart['PAY_DATE'])
# 筛选出日期为 2018-06-01 的记录（忽略时间部分）
df_shopcart = df_shopcart[df_shopcart['PAY_DATE'].dt.date == pd.to_datetime('2018-06-01').date()]

# 从 菜谱原始数据.xlsx 中加载数据
df_menu = pd.read_excel('菜谱原始数据.xlsx')

# 分别筛选出正域、零界、负域的顾客 ID
positive_domain_customers = df_customer[df_customer['仅节点中心性分类'] == '正域']['CUSTOMER_ID'].tolist()
zero_domain_customers = df_customer[df_customer['仅节点中心性分类'] == '零界']['CUSTOMER_ID'].tolist()
negative_domain_customers = df_customer[df_customer['仅节点中心性分类'] == '负域']['CUSTOMER_ID'].tolist()

# 随机选择正域、零界、负域各一个顾客 ID
positive_domain_customer_id = random.choice(positive_domain_customers) if positive_domain_customers else None
zero_domain_customer_id = random.choice(zero_domain_customers) if zero_domain_customers else None
negative_domain_customer_id = random.choice(negative_domain_customers) if negative_domain_customers else None

# 为正域顾客推荐购买频率最高的产品
if positive_domain_customer_id:
    customer_purchases = df_shopcart[df_shopcart['CUSTOMER_ID'] == positive_domain_customer_id]
    product_frequency = customer_purchases['PRODUCT_ID'].value_counts()
    top_products = product_frequency.index.tolist()
    print(f"为正域顾客 {positive_domain_customer_id} 推荐的产品: {top_products}")

# 协同过滤推荐函数
def collaborative_filtering_recommendation(target_customer_id, df_shopcart):
    # 构建顾客 - 产品矩阵
    customer_product_matrix = df_shopcart.pivot_table(index='CUSTOMER_ID', columns='PRODUCT_ID', aggfunc=lambda x: 1, fill_value=0)

    # 将矩阵转换为稀疏矩阵
    sparse_customer_product_matrix = csr_matrix(customer_product_matrix.values)

    # 计算顾客之间的相似度
    similarity_matrix = cosine_similarity(sparse_customer_product_matrix)

    # 获取目标顾客的索引
    target_customer_index = customer_product_matrix.index.get_loc(target_customer_id)

    # 获取与目标顾客最相似的顾客索引（排除自身）
    similar_customer_indices = similarity_matrix[target_customer_index].argsort()[::-1][1:]

    recommended_products = []
    for similar_customer_index in similar_customer_indices:
        similar_customer_id = customer_product_matrix.index[similar_customer_index]
        similar_customer_purchases = set(df_shopcart[df_shopcart['CUSTOMER_ID'] == similar_customer_id]['PRODUCT_ID'])
        target_customer_purchases = set(df_shopcart[df_shopcart['CUSTOMER_ID'] == target_customer_id]['PRODUCT_ID'])
        new_products = similar_customer_purchases - target_customer_purchases
        recommended_products.extend(list(new_products))
        if len(recommended_products) >= 5:  # 假设推荐 5 个产品
            break
    return recommended_products[:5]

# 菜谱食材推荐函数
def menu_ingredient_recommendation(target_customer_id, df_shopcart, df_menu):
    # 获取目标顾客在6月1日当天购买的产品名称
    customer_purchased_products = df_shopcart[
        (df_shopcart['CUSTOMER_ID'] == target_customer_id) &
        (df_shopcart['PAY_DATE'].dt.date == pd.to_datetime('2018-06-01').date())
    ]['PRODUCT_NAME'].tolist()

    recommended_ingredients = set()  # 使用集合避免重复推荐

    # 遍历菜谱原始数据中的每一行
    for _, row in df_menu.iterrows():
        # 假设食材在第一列，且食材之间用逗号分隔
        row_ingredients = set(row['食材'].split('，'))  # 使用中文逗号分隔食材
        common_ingredients = set()  # 用于存储与顾客购买产品名称匹配的食材

        # 遍历该行的食材，检查是否在顾客购买的产品名称中出现
        for ingredient in row_ingredients:
            for product_name in customer_purchased_products:
                if ingredient in product_name:  # 如果食材名称出现在产品名称中
                    common_ingredients.add(ingredient)
                    break

        # 如果匹配的食材数量大于等于2，则推荐该行中剩余的食材
        if len(common_ingredients) >= 2:
            remaining_ingredients = row_ingredients - common_ingredients
            # 推荐至多3个食材，并确保不重复
            recommended_ingredients.update(list(remaining_ingredients)[:3])

    # 将推荐的食材转换为列表并返回
    return list(recommended_ingredients)[:3]  # 最终返回至多3个不重复的食材

# 为零界顾客进行推荐
if zero_domain_customer_id:
    cf_recommended_products = collaborative_filtering_recommendation(zero_domain_customer_id, df_shopcart)
    menu_recommended_ingredients = menu_ingredient_recommendation(zero_domain_customer_id, df_shopcart, df_menu)
    print(f"为零界顾客 {zero_domain_customer_id} 协同过滤推荐的产品: {cf_recommended_products}，菜谱食材推荐的食材: {menu_recommended_ingredients}")

# 为负域顾客进行推荐
if negative_domain_customer_id:
    cf_recommended_products = collaborative_filtering_recommendation(negative_domain_customer_id, df_shopcart)
    menu_recommended_ingredients = menu_ingredient_recommendation(negative_domain_customer_id, df_shopcart, df_menu)
    print(f"为负域顾客 {negative_domain_customer_id} 协同过滤推荐的产品: {cf_recommended_products}，菜谱食材推荐的食材: {menu_recommended_ingredients}")