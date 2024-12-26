import os
import time
import json
import requests 
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed

# site
HOME_PAGE = 'https://tybsouthgym.xidian.edu.cn/Views/User/Main.html'
LOGIN = 'https://tybsouthgym.xidian.edu.cn/User/UserChoose?LoginType=1'
ORDER = 'https://tybsouthgym.xidian.edu.cn/Field/OrderField'

# params
START_TIME = '19:00'
END_TIME = '21:00'
Field = 'YMQ'  # PPQ or YMQ
START_NUM = 1   #场地编号
END_NUM = 10


def login():
    chrome_options = Options()
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    driver.get(LOGIN)
    input('请手动登录后在命令行按回车键继续')
    cookies = driver.get_cookies()
    with open('cookies.txt', 'w') as f:
        f.write(str(cookies))
    driver.quit()


def get_cookies():
    cookies_dict = {}
    if not os.path.exists('cookies.txt'):
        return cookies_dict
    with open('cookies.txt', 'r') as f:
        cookies = f.read()
        if not cookies:
            return cookies_dict
        cookies = eval(cookies)
        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']
    return cookies_dict

def judge_login(params):    
    cookies_dict = get_cookies()
    response = requests.post(ORDER, data=params, cookies=cookies_dict)
    print(response.text)
    if 'BackUrl' in response.url:
        print('登录过期/未登录，请重新登录')
        login()


def get_params(FieldNo):
    params = {
        'checkdata': '[{"FieldNo":"PPQ015","FieldTypeNo":"002","BeginTime":"18:00","Endtime":"18:00"}]',
        'dateadd': '2',
        'VenueNo': '01'
    }
    if not FieldNo:
        return params
    # 修改预定场地
    checkdata = params['checkdata']
    checkdata = json.loads(checkdata)
    checkdata[0]['FieldNo'] = FieldNo
    checkdata[0]['FieldTypeNo'] = '001' if 'YMQ' in FieldNo else '002'
    checkdata[0]['BeginTime'] = START_TIME
    checkdata[0]['Endtime'] = END_TIME
    params['checkdata'] = str(checkdata)
    dateadd = '2'  # 0 今天 1 明天 2 后天
    params['dateadd'] = dateadd
    return params

def make_request(params, cookies_dict):
    response = requests.post(ORDER, data=params, cookies=cookies_dict)
    return  params, response.text

def log_result(params, response_text):
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(str(params) + '\n' + response_text + '\n\n')


def main():
    params = get_params('')
    print(params)
    judge_login(params)
    cookies_dict = get_cookies()
    time.sleep(5)
    while True:
        #12:00之后开始预定
        if time.localtime().tm_hour >= 12:
            break
    with ThreadPoolExecutor(10) as executor:
        task = []
        for i in range(START_NUM, END_NUM+1):
            FieldNo = Field + str(i).zfill(3)
            params = get_params(FieldNo)
            task.append(executor.submit(make_request, params, cookies_dict))
        for future in as_completed(task):
            params, response_text = future.result()
            print(params, '\n', response_text,'\n')
            log_result(params, response_text)
    
    time.sleep(5)

    with ThreadPoolExecutor(10) as executor:
        task = []
        for i in range(START_NUM, END_NUM+1):
            FieldNo = Field + str(i).zfill(3)
            params = get_params(FieldNo)
            task.append(executor.submit(make_request, params, cookies_dict))
        for future in as_completed(task):
            params, response_text = future.result()
            print(params, '\n', response_text,'\n')
            log_result(params, response_text)

    for i in range(START_NUM, END_NUM+1):
        time.sleep(5)
        FieldNo = Field + str(i).zfill(3)
        params = get_params(FieldNo)
        response = requests.post(ORDER, data=params, cookies=cookies_dict)
        print(params, '\n',response.text,'\n')
        log_result(params, response.text)

if __name__ == '__main__':
    main()
