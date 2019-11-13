# 快代理：https://www.kuaidaili.com/free/
#
import requests
from bs4 import BeautifulSoup
import pandas as pd
import threading
import time
from time import sleep

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 代理是否成功测试网站
test_http = 'http://httpbin.org/get'
test_https = 'https://httpbin.org/get'

header = {
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Language': 'zh-CN',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'Keep-Alive',
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.01)'
}


def pandas_to_xlsx(filename, info):  # 储存到xlsx
    pd_look = pd.DataFrame(info)
    pd_look.to_excel(filename, sheet_name='快代理')


def TestOneProxy(ip, port, n):
    proxy = ip + ':' + port
    proxies = {
        'http': 'http://' + proxy,
        'https': 'https://' + proxy,
    }
    try:
        response = requests.get('http://httpbin.org/get', proxies=proxies, timeout=3)
        if response.status_code == 200:
            print(n, '--验证代理通过 ip', ip, ' 端口:', port)
            return True
        else:
            print(n, '--验证代理失败 ip', ip, ' 端口:', port)
            return False
    except BaseException as e:
        print(n, '--Error', e.args)
        return False


def getHttpsProxy(url):
    for i in range(1, 150):
        sleep(1)
        curUrl = url + str(i) + '/'
        try:
            print('正在获取代理信息，网页', curUrl)
            webcontent = requests.get(curUrl, verify=False)
            if webcontent.status_code != 200:
                print('获取错误网页,错误码:', webcontent.status_code)
                continue
            soup = BeautifulSoup(webcontent.text, 'html.parser')
            list = soup.select('#list')
            if len(list) == 0:
                print('获取错误网页,网页内容:', webcontent.text)
                continue
            a = list[0].select('tbody')[0]
            b = a.select('tr')
            for item in b:
                td = item.select('td')
                info = {}
                info['ip'] = td[0].text
                info['port'] = td[1].text
                info['匿名度'] = td[2].text
                info['类型'] = td[3].text
                info['位置'] = td[4].text
                info['响应速度'] = td[5].text
                info['最后验证时间'] = td[6].text
                allProxies.append(info)
        except requests.exceptions.ConnectionError as e:
            print('--Error', e.args)
            pandas_to_xlsx('所有代理.xlsx', allProxies)
    return allProxies


# 线程函数
num = 0


def threadFun(n):
    global num
    while True:

        # 领取任务
        lock.acquire()
        if num >= len(allProxies):
            lock.release()
            break
        curTestProxy = allProxies[num]
        num = num + 1
        lock.release()
        # 线程干活
        if TestOneProxy(curTestProxy['ip'], curTestProxy['port'], n):
            canUseProxies.append(curTestProxy)

    print(n, '--运行结束')


if __name__ == '__main__':
    allProxies = []
    canUseProxies = []

    # 单线程获取所有可用代理
    url = 'http://www.kuaidaili.com/free/inha/'
    getHttpsProxy(url)

    # 多线程测试是否可用
    lock = threading.Lock()
    res = []
    for i in range(15):  # 创建线程50个线程
        t = threading.Thread(target=threadFun, args=("thread-%s" % i,))
        t.start()
        res.append(t)
    for r in res:  # 循环线程实例列表，等待所有的线程执行完毕
        r.join()  # 线程执行完毕后，才会往后执行，相当于C语言中的wait()

    if len(canUseProxies) > 0:
        for proxy in canUseProxies:
            print("{\"https\": \"https://" + proxy["ip"] + ":" + proxy["port"] + "\", \"http\": \"http://" + proxy["ip"] + ":" + proxy["port"] + "\"}, ",
                  file=open("proxy.txt", "a", encoding="utf-8"))
        pandas_to_xlsx('所有可用代理.xlsx', canUseProxies)

print('end')
