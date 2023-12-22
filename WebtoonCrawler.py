import threading
import requests
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import concurrent.futures

class WebtoonCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.book_url = None
        self.chapter_info = []
        self.book_save_path = None
        self.chapter_iter = None
        self.chapter_iter_lock = threading.Lock()
        self.store_chapter_with_serial_number = False
    
    def get_headers(self):
        # 回傳除了圖片請求外的請求headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.webtoons.com/zh-hant/martial-arts/nanomasin-s3/list?title_no=5393',
            'Connection': 'keep-alive',
            'Cookie': 'needGDPR=false; needCCPA=false; needCOPPA=false; countryCode=TW; timezoneOffset=+8; ctZoneId=Asia/Taipei; rw=w_5393_30',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'TE': 'trailers'
        }
        return headers

    def set_book_url(self, book_url):
        self.book_url = book_url
        self.chapter_info = []  # 重置章節URL列表

    def set_book_save_path(self, book_save_path):
        self.book_save_path = book_save_path

    def fetch_paginat(self, now_page_url=None):
        if now_page_url is None:
            now_page_url = self.book_url

        response = requests.get(now_page_url, headers=self.get_headers())
        pagination_info = []

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            pagination_div = soup.find('div', class_='paginate')

            if pagination_div:
                pagination_links = pagination_div.find_all('a')
                base_url = "https://www.webtoons.com"
                next_page_url = None  # 用於儲存下一頁的 URL

                for link in pagination_links:
                    href = link.get('href')
                    page_number = link.text.strip()

                    # 檢查是否為 "下一頁" 的鏈接
                    if '下一頁' in page_number:
                        next_page_url = base_url + href
                        continue  # 跳過當前迴圈的迭代

                    # 忽略 "上一頁" 的鏈接
                    if '上一集' in page_number:
                        continue

                    if href == '#':
                        pagination_info.append({'url': now_page_url, 'page': int(page_number)})
                    elif href:
                        full_url = base_url + href
                        pagination_info.append({'url': full_url, 'page': int(page_number)})

                # 如果存在下一頁，遞迴調用 fetch_paginat 並合併結果
                if next_page_url:
                    pagination_info.extend(self.fetch_paginat(next_page_url))

        return pagination_info

    def fetch_chapter_urls(self, pagination_url):
        # 發送GET請求
        response = requests.get(pagination_url, headers=self.get_headers())

        # 確保請求成功
        if response.status_code == 200:
            # 使用BeautifulSoup解析HTML內容
            soup = BeautifulSoup(response.text, 'html.parser')

            # 找到所有包含章節信息的<li>元素
            episode_items = soup.find_all('li', class_='_episodeItem')

            # 提取每個章節的標題和URL
            for item in episode_items:
                title = item.find('span', class_='subj').get_text(strip=True)
                link = item.find('a')['href']
                self.chapter_info.append({'title': title, 'url': link})

    def fetch_all_chapter_info(self):
        pagination_info = self.fetch_paginat()
        for info in tqdm(pagination_info, desc="處理分頁"):
            # print(f"正在處理第{info['page']}頁")
            # print(f"URL: {info['url']}")
            self.fetch_chapter_urls(info['url'])
        
        # 為 self.chapter_info 中的每個項目建立 serial_number
        total_chapters = len(self.chapter_info)
        for index, chapter in enumerate(self.chapter_info, start=1):
            # 從後到前計算章節編號
            chapter['serial_number'] = total_chapters - index + 1

        # 根據 serial_number 進行排序
        self.chapter_info.sort(key=lambda x: x['serial_number'])

    def fetch_chapter_img_urls(self, chapter_url, session):

        # 發送HTTP請求
        response = session.get(chapter_url)

        image_urls = []

        # 確保請求成功
        if response.status_code == 200:
            # 解析HTML內容
            soup = BeautifulSoup(response.text, 'html.parser')

            # 找到特定ID的div
            div = soup.find('div', id='_imageList')

            # 檢查div是否存在
            if div:
                # 在div中找到所有圖片
                images = div.find_all('img')

                # 提取每個圖片的src屬性
                image_urls = [img['data-url'] for img in images]

        return image_urls

    def fetch_img(self, img_url, chapter_save_path, img_number, session):
        
        # 設定圖片儲存路徑
        img_save_path = f"{chapter_save_path}/{img_number}.jpg"  # 假設圖片為jpg格式
        
        # print(f"正在下載圖片: {img_save_path}")

        # 發送GET請求
        response = session.get(img_url)

        # 檢查請求是否成功
        if response.status_code == 200:
            # 將圖片內容寫入文件
            with open(img_save_path, 'wb') as file:
                file.write(response.content)
            
            # 更新進度
            with open(f"{chapter_save_path}/.progress", 'w') as progress_file:
                progress_file.write(str(img_number))

    def download_chapter(self, chatper):
        # 獲取章節的標題和URL
        chapter_title = chatper['title']
        chapter_url = chatper['url']

        # 設定章節儲存路徑
        if self.store_chapter_with_serial_number:
            chapter_save_path = f"{self.book_save_path}/{chatper['serial_number']} {chapter_title}"
        else:
            chapter_save_path = f"{self.book_save_path}/{chapter_title}"
        # 確保儲存目錄存在
        os.makedirs(chapter_save_path, exist_ok=True)

        # 檢查章節是否已經完成下載
        if os.path.exists(f"{chapter_save_path}/.completed"):
            print(f"章節 {chapter_title} 已經下載完成")
            return
        
        # 檢查進度
        start_img_number = 1
        progress_path = f"{chapter_save_path}/.progress"
        if os.path.exists(progress_path):
            with open(progress_path, 'r') as progress_file:
                start_img_number = int(progress_file.read()) + 1


        # 創建並配置一個新的 Session
        session = self.create_session()

        # 獲取章節的圖片URL
        img_urls = self.fetch_chapter_img_urls(chapter_url=chapter_url, session=session)


        # # 下載所有圖片(有進度條)
        # for img_number, url in tqdm(enumerate(img_urls[start_img_number - 1:], start=start_img_number), 
        #                             total=len(img_urls[start_img_number - 1:]), 
        #                             desc=f"章節 {chapter_title} ",
        #                             leave=False):
        #     # print(f"正在下載圖片: {url}")
        #     self.fetch_img(chapter_save_path=chapter_save_path, img_url=url, img_number=img_number, session=session)

        # 下載所有圖片(無進度條)
        for img_number, url in enumerate(img_urls[start_img_number - 1:], start=start_img_number):
            # print(f"正在下載圖片: {url}")
            self.fetch_img(chapter_save_path=chapter_save_path, img_url=url, img_number=img_number, session=session)

        # 關閉Session
        session.close()

        # 迴圈結束，顯示完成訊息
        print(f"章節 {chapter_title} 已經下載完成")

        # 標記章節為下載完成
        with open(f"{chapter_save_path}/.completed", 'w') as completed_file:
            completed_file.write("Completed")

        # 刪除進度檔案
        if os.path.exists(progress_path):
            os.remove(progress_path)
            # print(f"已刪除進度檔案: {progress_path}")

    def download_all_chapters(self, max_workers=1):
        # 使用線程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 為每個章節提交下載任務
            futures = [executor.submit(self.download_chapter, chapter) for chapter in self.chapter_info]

            # 等待所有任務完成並處理可能的錯誤
            for future in concurrent.futures.as_completed(futures):
                try:
                    # 嘗試獲取任務結果
                    result = future.result()
                    # 處理結果
                    # ...
                    pass
                except Exception as e:
                    # 處理發生在任務中的異常
                    print(f"任務執行過程中發生錯誤: {e}")

    def create_session(self):
        # 創建並配置一個新的 Session，用來發送圖片請求
        session = requests.Session()
        # 自定義請求頭部
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Accept': 'image/avif,image/webp,*/*',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.webtoons.com/',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'TE': 'trailers'
        }
        session.headers.update(headers)
        return session
    
    def use_serial_number(self, use_serial_number):
        self.store_chapter_with_serial_number = use_serial_number
