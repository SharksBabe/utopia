import json
import jieba
import jieba.analyse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def load_reviews():
    """
    加载评论数据
    :return: 评论数据列表
    """
    try:
        with open('resident_evil_requiem_reviews.json', 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        print(f"成功加载 {len(reviews)} 条评论")
        return reviews
    except Exception as e:
        print(f"加载评论数据失败: {e}")
        return []

def clean_text(text):
    """
    清洗文本
    :param text: 原始文本
    :return: 清洗后的文本
    """
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除特殊字符（使用Python re模块支持的语法）
    text = re.sub(r'[\s\W_]+', ' ', text)
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def segment_text(text):
    """
    文本分词
    :param text: 清洗后的文本
    :return: 分词结果
    """
    # 加载自定义词典（如果有）
    # jieba.load_userdict('custom_dict.txt')
    
    # 分词
    words = jieba.cut(text)
    # 过滤停用词
    stopwords = set()
    try:
        with open('stopwords.txt', 'r', encoding='utf-8') as f:
            stopwords = set([line.strip() for line in f])
    except:
        # 如果没有停用词文件，使用默认停用词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    
    filtered_words = [word for word in words if word not in stopwords and len(word) > 1]
    return filtered_words

def extract_keywords(text, topK=10):
    """
    提取关键词
    :param text: 清洗后的文本
    :param topK: 提取的关键词数量
    :return: 关键词列表
    """
    keywords = jieba.analyse.extract_tags(text, topK=topK, withWeight=False)
    return keywords

def classify_feedback(review):
    """
    分类反馈
    :param review: 评论数据
    :return: 分类结果
    """
    content = review.get('content', '')
    recommendation = review.get('recommendation', '')
    
    # 定义分类关键词
    categories = {
        '画面': ['画面', '画质', '视觉', '特效', '场景', '画面精美', '画面震撼'],
        '剧情': ['剧情', '故事', '情节', '叙事', '结局', '剧情紧凑', '剧情精彩'],
        '玩法': ['玩法', '操作', '系统', '机制', '玩法创新', '操作流畅'],
        '音效': ['音效', '音乐', '配音', '声音', '音效震撼', '音乐好听'],
        '性能': ['性能', '优化', '卡顿', '流畅度', '帧率', '优化好'],
        '价格': ['价格', '性价比', '贵', '便宜', '性价比高', '价格合理'],
        'bug': ['bug', '错误', '问题', '崩溃', 'bug多', '问题多'],
        '推荐': ['推荐', '值得', '必玩', '好评', '强烈推荐', '值得购买']
    }
    
    # 初始化分类结果
    classification = {
        'category': '其他',
        'sentiment': '中性'
    }
    
    # 分析情感倾向
    if recommendation == '推荐':
        classification['sentiment'] = '正面'
    elif recommendation == '不推荐':
        classification['sentiment'] = '负面'
    
    # 分析分类
    max_count = 0
    for category, keywords in categories.items():
        count = sum(1 for keyword in keywords if keyword in content)
        if count > max_count:
            max_count = count
            classification['category'] = category
    
    return classification

def visualize_reviews(reviews):
    """
    可视化评论数据
    :param reviews: 评论数据列表
    """
    # 转换为DataFrame
    df = pd.DataFrame(reviews)
    
    # 1. 情感分布
    plt.figure(figsize=(8, 6))
    sentiment_counts = df['recommendation'].value_counts()
    sns.barplot(x=sentiment_counts.index, y=sentiment_counts.values)
    plt.title('评论情感分布')
    plt.xlabel('情感')
    plt.ylabel('数量')
    plt.savefig('sentiment_distribution.png')
    plt.show()
    
    # 2. 游戏时长分布
    plt.figure(figsize=(10, 6))
    sns.histplot(df['hours'], bins=20)
    plt.title('游戏时长分布')
    plt.xlabel('游戏时长（小时）')
    plt.ylabel('数量')
    plt.savefig('playtime_distribution.png')
    plt.show()
    
    # 3. 玩家等级分布
    plt.figure(figsize=(10, 6))
    sns.histplot(df['player_level'], bins=20)
    plt.title('玩家等级分布')
    plt.xlabel('玩家等级')
    plt.ylabel('数量')
    plt.savefig('player_level_distribution.png')
    plt.show()
    
    # 4. 拥有游戏数量分布
    plt.figure(figsize=(10, 6))
    sns.histplot(df['owned_games'], bins=20)
    plt.title('拥有游戏数量分布')
    plt.xlabel('拥有游戏数量')
    plt.ylabel('数量')
    plt.savefig('owned_games_distribution.png')
    plt.show()
    
    # 5. 分类分布
    categories = []
    sentiments = []
    for review in reviews:
        classification = classify_feedback(review)
        categories.append(classification['category'])
        sentiments.append(classification['sentiment'])
    
    df['category'] = categories
    df['sentiment'] = sentiments
    
    plt.figure(figsize=(12, 6))
    category_counts = df['category'].value_counts()
    sns.barplot(x=category_counts.index, y=category_counts.values)
    plt.title('评论分类分布')
    plt.xlabel('分类')
    plt.ylabel('数量')
    plt.xticks(rotation=45)
    plt.savefig('category_distribution.png')
    plt.show()
    
    # 6. 情感-分类交叉分析
    plt.figure(figsize=(12, 6))
    cross = pd.crosstab(df['category'], df['sentiment'])
    cross.plot(kind='bar', stacked=True)
    plt.title('情感-分类交叉分析')
    plt.xlabel('分类')
    plt.ylabel('数量')
    plt.xticks(rotation=45)
    plt.legend(title='情感')
    plt.savefig('sentiment_category_cross.png')
    plt.show()

def generate_wordcloud(reviews):
    """
    生成词云
    :param reviews: 评论数据列表
    """
    from wordcloud import WordCloud
    
    # 合并所有评论内容
    all_content = ' '.join([review.get('content', '') for review in reviews])
    
    # 清洗文本
    cleaned_content = clean_text(all_content)
    
    # 分词
    words = segment_text(cleaned_content)
    
    # 生成词云
    wordcloud = WordCloud(
        font_path='simhei.ttf',  # 中文字体路径
        width=800,
        height=600,
        background_color='white',
        max_words=200,
        max_font_size=100,
        random_state=42
    )
    
    # 统计词频
    word_counts = Counter(words)
    wordcloud.generate_from_frequencies(word_counts)
    
    # 保存词云
    plt.figure(figsize=(12, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('评论词云')
    plt.savefig('wordcloud.png')
    plt.show()

def main():
    """
    主函数
    """
    # 加载评论数据
    reviews = load_reviews()
    
    if not reviews:
        print("没有评论数据，无法进行分析")
        return
    
    # 数据清洗和分词
    for review in reviews:
        content = review.get('content', '')
        cleaned_content = clean_text(content)
        review['cleaned_content'] = cleaned_content
        review['words'] = segment_text(cleaned_content)
        review['keywords'] = extract_keywords(cleaned_content)
        
        # 分类
        classification = classify_feedback(review)
        review['category'] = classification['category']
        review['sentiment'] = classification['sentiment']
    
    # 保存处理后的数据
    with open('processed_reviews.json', 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print("处理后的数据已保存到 processed_reviews.json")
    
    # 可视化
    visualize_reviews(reviews)
    
    # 生成词云
    try:
        generate_wordcloud(reviews)
    except Exception as e:
        print(f"生成词云失败: {e}")
    
    # 统计分析
    print("\n=== 统计分析 ===")
    total_reviews = len(reviews)
    positive_reviews = sum(1 for review in reviews if review.get('sentiment') == '正面')
    negative_reviews = sum(1 for review in reviews if review.get('sentiment') == '负面')
    neutral_reviews = sum(1 for review in reviews if review.get('sentiment') == '中性')
    
    print(f"总评论数: {total_reviews}")
    print(f"正面评论: {positive_reviews} ({positive_reviews/total_reviews*100:.1f}%)")
    print(f"负面评论: {negative_reviews} ({negative_reviews/total_reviews*100:.1f}%)")
    print(f"中性评论: {neutral_reviews} ({neutral_reviews/total_reviews*100:.1f}%)")
    
    # 分类统计
    category_counts = Counter([review.get('category') for review in reviews])
    print("\n=== 分类统计 ===")
    for category, count in category_counts.items():
        print(f"{category}: {count} ({count/total_reviews*100:.1f}%)")

if __name__ == "__main__":
    main()
