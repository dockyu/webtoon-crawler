# webtoon-crawler
 a high performance webtoon crawler

## 使用
在[`main.py`](./main.py)設定必要資訊
+ `book_url`: 要下載的漫畫的首頁
    + ex: [`https://www.webtoons.com/zh-hant/city-office/newface/list?title_no=1759`](https://www.webtoons.com/zh-hant/city-office/newface/list?title_no=1759)
+ `book_save_path`: 要下載到哪個資料夾
+ `thread_num`: 要開幾個線程來下載
    + 基本上網路越好就可以開越多線程提升下載速度
    + 測試在下載速度*947.50 Mbps*時，開*4*個線程可以有很高的效率
+ `use_serial_number`: 章節的資料夾名稱要不要加上前綴
    + 如果要下載的漫畫章節名稱無法分辨前後順序(ex: [盜臉人生](https://www.webtoons.com/zh-hant/city-office/newface/list?title_no=1759))，可以設為True，會自動幫章節編號方便排序
