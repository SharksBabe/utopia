import json
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def get_steam_reviews(appid, max_reviews=100):
    """
    使用Selenium获取Steam游戏评论
    :param appid: 游戏的AppID
    :param max_reviews: 最大评论数量
    :return: 评论列表
    """
    reviews = []
    
    # 配置浏览器
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # 使用webdriver-manager自动管理EdgeDriver
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    
    try:
        # 打开游戏评论页面
        url = f"https://store.steampowered.com/app/{appid}/#app_reviews_hash"
        print(f"打开页面: {url}")
        driver.get(url)
        
        # 等待页面加载
        time.sleep(5)
        
        # 选择中文评论
        try:
            language_selector = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'language_filter'))
            )
            language_selector.click()
            time.sleep(2)
            
            # 选择简体中文
            chinese_option = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='popup_menu_item' and text()='简体中文']"))
            )
            chinese_option.click()
            time.sleep(5)
        except Exception as e:
            print(f"设置语言时出错: {e}")
        
        # 滚动加载更多评论
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while len(reviews) < max_reviews:
            # 提取当前页面的评论
            review_elements = driver.find_elements(By.XPATH, "//div[@class='review_box']")
            
            for review_elem in review_elements:
                if len(reviews) >= max_reviews:
                    break
                
                try:
                    # 提取评论内容
                    content_elem = review_elem.find_element(By.XPATH, ".//div[@class='review_body']")
                    content = content_elem.text.strip()
                    
                    # 提取推荐状态
                    recommendation_elem = review_elem.find_element(By.XPATH, ".//div[@class='review_header']")
                    recommendation_text = recommendation_elem.text
                    voted_up = '推荐' in recommendation_text
                    
                    # 提取游戏时长
                    hours_elem = review_elem.find_element(By.XPATH, ".//div[@class='reviewer_info']")
                    hours_text = hours_elem.text
                    hours_match = re.search(r'玩了 ([\d.]+) 小时', hours_text)
                    playtime_minutes = int(float(hours_match.group(1)) * 60) if hours_match else 0
                    
                    # 提取发布日期
                    date_elem = review_elem.find_element(By.XPATH, ".//div[@class='review_date']")
                    date_text = date_elem.text
                    # 这里需要根据实际日期格式进行解析
                    timestamp = int(time.time())  # 暂时使用当前时间戳
                    
                    # 提取玩家信息
                    steamid = ""
                    try:
                        user_link = review_elem.find_element(By.XPATH, ".//a[@class='persona_name']")
                        user_url = user_link.get_attribute('href')
                        # 从URL中提取Steam ID
                        steamid_match = re.search(r'profiles/(\d+)', user_url)
                        if steamid_match:
                            steamid = steamid_match.group(1)
                    except Exception as e:
                        print(f"获取玩家ID时出错: {e}")
                    
                    # 构建评论对象，保持与原API返回格式一致
                    review = {
                        'recommendationid': f"{len(reviews) + 1}",
                        'author': {
                            'steamid': steamid,
                            'playtime_forever': playtime_minutes,
                            'playtime_last_two_weeks': 0
                        },
                        'voted_up': voted_up,
                        'review': content,
                        'timestamp_created': timestamp,
                        'timestamp_updated': timestamp,
                        'comment_count': 0,
                        'steam_purchase': True,
                        'received_for_free': False,
                        'written_during_early_access': False
                    }
                    
                    reviews.append(review)
                    print(f"已获取 {len(reviews)} 条评论")
                    
                except Exception as e:
                    print(f"提取评论时出错: {e}")
            
            # 滚动到底部加载更多评论
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # 检查是否到达页面底部
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
    except Exception as e:
        print(f"获取评论时出错: {e}")
    finally:
        driver.quit()
    
    print(f"获取评论完成，共获取 {len(reviews)} 条评论")
    return reviews

def get_player_info(steamid):
    """
    获取玩家的Steam个人资料信息
    :param steamid: 玩家的Steam ID
    :return: 包含等级、完美通关游戏数量和拥有游戏数量的字典
    """
    player_info = {
        'level': 0,
        'perfect_games': 0,
        'owned_games': 0
    }
    
    # 添加请求头，模拟浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive'
    }
    
    try:
        # 获取玩家等级
        level_url = f"https://steamcommunity.com/profiles/{steamid}/?l=english"
        retries = 3
        for attempt in range(retries):
            try:
                level_response = requests.get(level_url, headers=headers, timeout=15)
                if level_response.status_code == 200:
                    # 提取等级信息
                    level_match = re.search(r'Level (\d+)', level_response.text)
                    if level_match:
                        player_info['level'] = int(level_match.group(1))
                break
            except Exception as e:
                print(f"获取玩家等级时出错: {e}")
                if attempt < retries - 1:
                    print(f"等待 3 秒后重试...")
                    time.sleep(3)
                else:
                    print("获取玩家等级失败")
        
        # 等待一段时间再请求游戏库信息
        time.sleep(2)
        
        # 获取玩家游戏库信息
        games_page_url = f"https://steamcommunity.com/profiles/{steamid}/games/?tab=all"
        for attempt in range(retries):
            try:
                games_response = requests.get(games_page_url, headers=headers, timeout=15)
                if games_response.status_code == 200:
                    # 提取拥有的游戏数量
                    games_count_match = re.search(r'(\d+) games', games_response.text)
                    if games_count_match:
                        player_info['owned_games'] = int(games_count_match.group(1))
                    
                    # 提取完美通关游戏数量（通过成就100%的游戏）
                    # 注意：这个信息可能需要更复杂的处理
                    # 这里暂时设置为0，实际使用时需要根据网页结构调整
                    player_info['perfect_games'] = 0
                break
            except Exception as e:
                print(f"获取玩家游戏库信息时出错: {e}")
                if attempt < retries - 1:
                    print(f"等待 3 秒后重试...")
                    time.sleep(3)
                else:
                    print("获取玩家游戏库信息失败")
        
        # 避免请求过于频繁
        time.sleep(2)
        
    except Exception as e:
        print(f"获取玩家信息时出错: {e}")
    
    return player_info

def process_reviews(reviews):
    """
    处理评论数据，提取有用信息
    :param reviews: 原始评论列表
    :return: 处理后的评论列表
    """
    import datetime
    processed_reviews = []
    
    for review in reviews:
        # 转换时间戳为YYYY-MM-DD格式
        timestamp = review.get('timestamp_created', 0)
        publish_date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        # 提取游戏总时长（分钟转换为小时）
        playtime_minutes = review.get('author', {}).get('playtime_forever', 0)
        hours = round(playtime_minutes / 60, 1)
        
        # 推荐状态
        recommendation = '推荐' if review.get('voted_up', False) else '不推荐'
        
        # 获取玩家信息
        steamid = review.get('author', {}).get('steamid')
        player_info = get_player_info(steamid) if steamid else {
            'level': 0,
            'perfect_games': 0,
            'owned_games': 0
        }
        
        processed_review = {
            'publish_date': publish_date,
            'content': review.get('review', ''),
            'recommendation': recommendation,
            'hours': hours,
            'player_level': player_info['level'],
            'owned_games': player_info['owned_games']
        }
        processed_reviews.append(processed_review)
    
    return processed_reviews

def save_reviews_to_file(reviews, filename):
    """
    保存评论到文件
    :param reviews: 评论列表
    :param filename: 文件名
    """
    # 保存为JSON文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"评论已保存到 {filename}")
    
    # 保存为Excel文件
    excel_filename = filename.replace('.json', '.xlsx')
    try:
        df = pd.DataFrame(reviews)
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        print(f"评论已保存到 {excel_filename}")
    except Exception as e:
        print(f"保存为Excel文件时出错: {e}")
        print("请确保已安装openpyxl库: pip install openpyxl")

if __name__ == "__main__":
    # Resident Evil Requiem 的 AppID
    appid = 3764200
   
    print("开始使用Selenium获取 Resident Evil Requiem 的评论...")
    print(f"游戏AppID: {appid}")
    
    reviews = get_steam_reviews(appid, max_reviews=50)
    
    print(f"共获取到 {len(reviews)} 条评论")
    
    if reviews:
        processed_reviews = process_reviews(reviews)
        save_reviews_to_file(processed_reviews, 'resident_evil_requiem_reviews.json')
    else:
        print("未获取到评论")
        print("可能的原因：1. 游戏刚发售还没有评论 2. 网络连接问题 3. AppID错误")
