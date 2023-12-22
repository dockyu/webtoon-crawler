from WebtoonCrawler import WebtoonCrawler

# 設置漫畫首頁的URL
book_url = r'https://www.webtoons.com/zh-hant/city-office/newface/list?title_no=1759'
# 設置漫畫保存的路徑
book_save_path = r'D:/store/webtoon/盜臉人生'
# 設置線程數量，推薦值為4
thread_num = 4
# 是否使用章節編號作為章節資料夾的前綴，原本的章節名稱看不出先後順序的話，可以設置為True
use_serial_number = True

if __name__ == '__main__':

    crawler = WebtoonCrawler()

    # 設定
    crawler.set_book_url(book_url=book_url)
    crawler.set_book_save_path(book_save_path=book_save_path)
    crawler.use_serial_number(use_serial_number=use_serial_number)

    # 獲取所有章節的URL
    crawler.fetch_all_chapter_info()

    # 開始下載所有章節
    crawler.download_all_chapters(max_workers=thread_num)  # 可以根據需要調整線程數量