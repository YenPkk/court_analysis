from selenium.webdriver.chrome.service import Service
from selenium import webdriver

# 處理逾時例外的工具
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException


# 面對動態網頁，等待某個元素出現的工具，通常與 exptected_conditions 搭配
from selenium.webdriver.support.ui import WebDriverWait

# 搭配 WebDriverWait 使用，對元素狀態的一種期待條件，若條件發生，則等待結束，往下一行執行
from selenium.webdriver.support import expected_conditions as EC

# 期待元素出現要透過什麼方式指定，通常與 EC、WebDriverWait 一起使用
from selenium.webdriver.common.by import By

# 強制等待 (執行期間休息一下)
from time import sleep

#beautifulsoup
import requests as req
from bs4 import BeautifulSoup as bs
from pprint import pprint

import re

import json

import pandas as pd

# 加入行為鍊 ActionChain (在 WebDriver 中模擬滑鼠移動、點擊、拖曳、按右鍵出現選單，以及鍵盤輸入文字、按下鍵盤上的按鈕等)
from selenium.webdriver.common.action_chains import ActionChains

# 加入鍵盤功能 (例如 Ctrl、Alt 等)
from selenium.webdriver.common.keys import Keys

# 設定log檔案
import logging
logger = logging.getLogger('Taiwan_court_kill_cases_v2.log')
logger.setLevel(logging.INFO) 

# 設定輸出格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

# 儲存在 log 當中的事件處理器(存在.log檔中)
fileHandler = logging.FileHandler('Taiwan_court_kill_cases', mode='a', encoding='utf-8') # a: append, w: write  #建構方法
fileHandler.setFormatter(formatter)

# 輸出在終端機介面上的事件處理器
console_handler = logging.StreamHandler()  #建構方法
console_handler.setFormatter(formatter)    #將物件設定格式(這邊的formatter)

# 加入事件
logger.addHandler(console_handler)         #addHandler也就是說，這個logger物件要要如何處理log訊息
logger.addHandler(fileHandler)

# 處理日期的list 一組組搜尋寫成一個list這樣用index就可以搜尋了也比較好處理
all_split_date_combination_list = []
# 簡單生這樣就好[85,1,1, 6,30], [85,7,1,12,31]
for i in range(113,84, -1): # 民國113到85
    month_day_list = [[7,1,12,31], [1,1, 6,30]]
    for b in month_day_list:
        b.insert(0, i)
        all_split_date_combination_list.append(b)

driver = webdriver.Chrome()

# 放所有case的資料
all_case_list = []
# 每次查詢的總頁數網址
page_url_list = []
# 給每個case一個數字的primary key id
id_id = 1
# 每爬超過500筆，休息一下
rest_time_count = 1

####這邊主程式

# 以切分日期的方式爬取所有資料
for date_split in all_split_date_combination_list:  #從113年取回來
    
    # 每爬超過500筆，休息一下
    if (len(all_case_list)/500) >= rest_time_count:
        logger.info(f"total cases:{len(all_case_list)}, rest 5 mins")
        sleep(300)
        rest_time_count += 1

    driver.get("https://judgment.judicial.gov.tw/FJUD/Default_AD.aspx")
    # 搜尋
    try:
        WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input#jud_jmain')
        ))
        input_case_reason = driver.find_element(By.CSS_SELECTOR, 'input#jud_jmain')
        input_case_reason.clear()   
        input_case_reason.send_keys("殺人")
        
        input_case_content = driver.find_element(By.CSS_SELECTOR, 'input#jud_kw')
        input_case_content.clear()
        input_case_content.send_keys("中華民國刑法第 271 條&刑事判決")
        
        input_date_from_year = driver.find_element(By.CSS_SELECTOR, 'input#dy1')
        input_date_from_month = driver.find_element(By.CSS_SELECTOR, 'input#dm1')
        input_date_from_day = driver.find_element(By.CSS_SELECTOR, 'input#dd1')

        input_date_end_year = driver.find_element(By.CSS_SELECTOR, 'input#dy2')
        input_date_end_month = driver.find_element(By.CSS_SELECTOR, 'input#dm2')
        input_date_end_day = driver.find_element(By.CSS_SELECTOR, 'input#dd2')

        input_date_from_year.clear()
        input_date_from_month.clear()
        input_date_from_day.clear()
        input_date_end_year.clear()
        input_date_end_month.clear()
        input_date_end_day.clear()

        # 開始輸入數字
        ac = ActionChains(driver)
        ac.send_keys_to_element(input_date_from_year, date_split[0])
        ac.send_keys_to_element(input_date_from_month, date_split[1])
        ac.send_keys_to_element(input_date_from_day, date_split[2])
        ac.send_keys_to_element(input_date_end_year, date_split[0])
        ac.send_keys_to_element(input_date_end_month, date_split[3])
        ac.send_keys_to_element(input_date_end_day, date_split[4])


        # 執行
        ac.perform()
        sleep(1)
        search_button = driver.find_element(By.CSS_SELECTOR, 'input#btnQry')
        search_button.click()
        logger.info(f"{date_split} is search")
        sleep(1)
    except TimeoutException:
        logger.warning(f"{date_split} can not search")
        continue
    
    #等待iframe與下一頁按鈕，計算pages
    try:
        WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
        (By.CSS_SELECTOR, "iframe#iframe-data")
        ))

        iframe = driver.find_element(By.CSS_SELECTOR, "iframe#iframe-data")
        one_page_url = iframe.get_attribute('src')  #切到iframe裡面就會抓不到了....要先抓....
        logger.info(f"search {date_split}, it's base url is {one_page_url}")
        driver.switch_to.frame(iframe)
    except TimeoutException:
        logger.info(f"{date_split} not found result, do next search") #若iframe抓不到表示沒有搜尋結果，就往下搜下一個就好
        continue                                                      # 還是會有iframe只是結果是error page，結論是不管這邊有沒有處理都可以繼續拉，但怎麼樣可以讓他直接跳出此迴圈呢?
    except StaleElementReferenceException:
        logger.info(f"{date_split} not found result, do next search")
        continue


    only_one_page = False
    try:
        # 如果沒抓到這個，很可能只有一頁，那麼下面製造pages就不做了，程式也會在這裡斷開，交給下面有個if處理，若這種情況發生就去抓原本iframe的網址，只有一頁加入page_url_list這樣
        WebDriverWait(driver, 10).until(  #看這邊時間要不要設晚一點?
        EC.presence_of_element_located(
        (By.CSS_SELECTOR, "a#hlNext")
        ))

        page_url = driver.find_element(By.CSS_SELECTOR, 'a#hlNext').get_attribute('href')

        #計算頁數，與生成page_list
        how_many_page = driver.find_element(By.CSS_SELECTOR, "div#plPager span")
        page_re = "\d*(?=\s頁)"
        answer_page = re.search(page_re, how_many_page.text)
        page_url_list.clear()
        regex_page_url = "&page=[\d]*"
        test = re.split(regex_page_url, page_url)
        if int(answer_page[0]) <= 25:
            for each_page in range(1,int(answer_page[0])+1):
                page_url_list.append(f"{test[0]}&page={each_page}{test[1]}") 
        else:
            logger.warning(f"{date_split} need to minimize split date interval, otherwise data shortage!!")
            for each_page in range(1, 26):
                page_url_list.append(f"{test[0]}&page={each_page}{test[1]}")
                
            #這邊寫得好的話若超過25頁就要回到一開始的搜尋頁面，並把日期格式再切小
            # 妥協的辦法就是超過25就給他25頁就好

    except TimeoutException:
        only_one_page = True
        logger.info(f"{date_split} not found...next_page_button and pages or may be it has only one page")
    except StaleElementReferenceException:
        only_one_page = True
        logger.info(f"{date_split} not found...next_page_button and pages or may be it has only one page")


    if only_one_page:
        page_url_list.clear()
        page_url_list.append(one_page_url) 

    #計算一個搜尋的case數量並計算
    case_counter = 1 
    for page in page_url_list:
        driver.get(page)

        
        try:
            cssSelector = 'a#hlTitle'
            WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, cssSelector)
            ))

            case_url = driver.find_elements(By.CSS_SELECTOR, cssSelector)
            case_url_list = []
            for case in case_url:
                case_url_list.append(case.get_attribute('href'))
            
        except TimeoutException:
            # 這裡反而是抓到，沒有搜尋結果的錯誤
            logger.warning(f"{page} cases not found, may be there is no search result") #我在想這可能根本抓不到，抓到就跳出怎會到click??
            continue

        # cases找到後開始一個一個點
        # 這是每一頁當中的至多20筆的資料   
        for case_u in case_url_list:      
            driver.get(case_u)          # 這邊若有問題可以試試看改抓網址，然後用driver.get()處理

            try:
                # 看有沒有抓到js生成的側攔"當中的li"，li就是js後來生成的
                # 這邊要改可能還是沒有laws，而且結果超奇怪....根本抓不到law結果欄位有值，抓地到history但沒有值...
                
                side_li_selector_2 = 'div#JudHis div.panel-body ul li'
                WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                (By.CSS_SELECTOR, side_li_selector_2)
                ))

                #還是這邊可以等兩個?等個兩個載好在來取得動態html

            except TimeoutException:
                # 如果有錯的話抓這個webelement的text(標題)，href(超連結)
                logger.info(f"{id_id}:{case_u} not found...history, may be critical error")
                driver.refresh()
                sleep(10)
                #這邊之後要改logging
            except StaleElementReferenceException:   # Except 中不能再用webdriver了，不然抓不到又抱錯(不然就是要用簡單的等待錯略，部會丟exception那種)，給他refresh，不然就直接繼續抓就好，空的就空的
                logger.info(f"{id_id}:{case_u} driver refresh to relocated")
                driver.refresh()
                sleep(10)
                    

            try:   
                # 但這個欄位真的有可能抓不到那就要抱錯，可是我們應該分開來報，因為兩個的問題不一樣
                # 這邊不只會有TimeoutException，還有其他的所以會抱錯嘗試refresh，重抓看看
                side_li_selector_1 = 'ul.rela-law li'   #這邊真的很吃網路，其實也不算錯，就是網路加仔問題而已，但好像有點難解決
                WebDriverWait(driver, 10).until(    # 我還是不懂這邊怎麼會timeoutexception，不是用try except包起來了嗎????因為這邊抓到TimeoutException之後又raise了StaleElementReferenceException，所以不是沒抓到，而是因為StaleElementReferenceException而停的
                EC.presence_of_element_located(
                (By.CSS_SELECTOR, side_li_selector_1)
                ))

            #我之前有疑問，問什麼timeoutexception還會raise StaleElementReferenceException，這是因為我可能有點誤解timeoutexception了，timeoutexception是"網頁加載時間"上的問題，根本沒有加載完成所以沒辦法找到該元素，而StaleElementReferenceException是網頁加載"完"出現的元素定位問題(舉個例子就是，因為一些問題導致某個元素沒有出現在DOM TREE當中，所以根本找不到該元素)(在此情境中，就是"相關法條"常常跑不出來，但只要刷新頁面就可以解決了)所以當抓到StaleElementReferenceException，我就driver.refresh()，刷新看看，刷新之後也不做判斷了，就繼續往下做，沒有的欄位就空著
            # 所以WebDriverWait，TimeoutException, StaleElementReferenceException都會丟出來啦
            except TimeoutException:
                logger.info(f"{id_id}:{case_u} not found...laws, it's ok")
                driver.refresh() # 如果等不到就refresh，畢竟這邊也只是再判斷有沒有而已
                sleep(10)
            except StaleElementReferenceException:
                logger.info(f"{id_id}:{case_u} driver refresh to relocated")
                driver.refresh()
                sleep(10)


            #取得動態html #反正都要連到這個case當中，若上面兩個沒抓到，就只是side_bar的資料有少但其他資料還是有的
            #但我就在想這樣會不會很雞肋、而且反而拖到時間，因為有些case是真的沒有上面那兩個side_bar，還是乾脆就強制等待sleep算了，不知道哪種比較優且快
            sleep(1) # 稍微等一下laws那個side_bar位置
            case_html = driver.page_source
            soup = bs(case_html, "lxml")

            allSelector = 'div.col-td'
            all = soup.select(allSelector)

            laws_list = []
            linesSelector = 'ul.rela-law li'
            lines = soup.select(linesSelector)
            for law in lines:
                laws_list.append(str(law.get_text()))

            
            history_judgement = soup.select("div#JudHis div.panel-body ul li")
            history_judgement_list = []
            for index in range(0, len(history_judgement)):
                if not str(history_judgement[index].select_one('a')) == "None":
                    history_judgement_list.append({
                        "case_id":str(history_judgement[index].get_text()),
                        "url":"https://judgment.judicial.gov.tw/FJUD/"+ str(history_judgement[index].select_one('a')['href'])
                    })
                else:
                    history_judgement_list.append({
                    "case_id":str(history_judgement[index].get_text())
                    })


            all_case_list.append({
            "id_id":id_id,
            "case_id":str(all[0].get_text().strip()),
            "case_url":str(case_u),
            "date":str(all[1].get_text().strip()),
            "simple_reason":str(all[2].get_text().strip()),
            "laws":laws_list,
            "history_judgement":history_judgement_list,
            "context":str(all[3].get_text()),
            })
            
            logger.info(f"id_id:{id_id}, search {date_split}, case_number:{case_counter} is ok")
            id_id += 1
            case_counter += 1

# 就寫成dataframe再轉成csv八
tt = pd.DataFrame(all_case_list)
tt.to_csv('./all_cases_v3.csv', index=False)

