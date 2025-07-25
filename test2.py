import pandas as pd
import random
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

# 从 customer_network_analysis_20180601(1).xlsx 中读取数据
excel_file = pd.ExcelFile('customer_network_analysis_20180602(1).xlsx')
df_customer = excel_file.parse('Sheet1')

# 从 shopcart.xlsx 中加载数据
df_shopcart = pd.read_excel('shopcart.xlsx')
# 确保 PAY_DATE 列是日期时间格式
df_shopcart['PAY_DATE'] = pd.to_datetime(df_shopcart['PAY_DATE'])
# 筛选出日期为 2018-06-01 的记录（忽略时间部分）
df_shopcart = df_shopcart[df_shopcart['PAY_DATE'].dt.date == pd.to_datetime('2018-06-02').date()]

# 从 菜谱原始数据.xlsx 中加载数据
df_menu = pd.read_excel('菜谱原始数据.xlsx')

# 创建产品ID到产品名称的映射字典
product_id_to_name = df_shopcart.set_index('PRODUCT_ID')['PRODUCT_NAME'].to_dict()

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
    # 将推荐的产品ID转换为产品名称
    return [product_id_to_name.get(pid, "未知产品") for pid in recommended_products[:5]]

# 菜谱食材推荐函数
def menu_ingredient_recommendation(target_customer_id, df_shopcart, df_menu):
    # 获取目标顾客在6月1日当天购买的产品名称
    customer_purchased_products = df_shopcart[
        (df_shopcart['CUSTOMER_ID'] == target_customer_id) &
        (df_shopcart['PAY_DATE'].dt.date == pd.to_datetime('2018-06-02').date())
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

# 为指定顾客进行推荐
def recommend_for_customer(target_customer_id):
    # 检查输入的顾客ID是否存在于数据中
    if target_customer_id not in df_customer['CUSTOMER_ID'].values:
        print(f"顾客ID {target_customer_id} 不存在于数据中。")
        return

    # 获取顾客的节点中心性分类
    customer_domain = df_customer[df_customer['CUSTOMER_ID'] == target_customer_id]['仅购买分类'].values[0]
    print(f"顾客ID {target_customer_id} 属于 {customer_domain}。")

    # 根据顾客的节点中心性分类进行推荐
    if customer_domain == '正域':
        customer_purchases = df_shopcart[df_shopcart['CUSTOMER_ID'] == target_customer_id]
        product_frequency = customer_purchases['PRODUCT_ID'].value_counts()
        top_products = product_frequency.index.tolist()
        # 将推荐的产品ID转换为产品名称
        top_product_names = [product_id_to_name.get(pid, "未知产品") for pid in top_products]
        print(f"为正域顾客 {target_customer_id} 推荐的产品: {top_product_names}")
    elif customer_domain == '零界':
        cf_recommended_products = collaborative_filtering_recommendation(target_customer_id, df_shopcart)
        menu_recommended_ingredients = menu_ingredient_recommendation(target_customer_id, df_shopcart, df_menu)
        print(f"为零界顾客 {target_customer_id} 协同过滤推荐的产品: {cf_recommended_products}，菜谱食材推荐的食材: {menu_recommended_ingredients}")
    elif customer_domain == '负域':
        cf_recommended_products = collaborative_filtering_recommendation(target_customer_id, df_shopcart)
        menu_recommended_ingredients = menu_ingredient_recommendation(target_customer_id, df_shopcart, df_menu)
        print(f"为负域顾客 {target_customer_id} 协同过滤推荐的产品: {cf_recommended_products}，菜谱食材推荐的食材: {menu_recommended_ingredients}")
    else:
        print(f"顾客ID {target_customer_id} 的分类 {customer_domain} 不在正域、零界或负域中。")

# 输入顾客ID并获取推荐结果
input_customer_id = int(input("请输入顾客ID: "))
recommend_for_customer(input_customer_id)