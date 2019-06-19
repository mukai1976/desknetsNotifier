#coding:UTF-8

#libraries needs to be installed
#selenium, pyyaml, slackclient, bs4, lxml
# and phantomjs

# get ChromeDriver from here
# https://sites.google.com/a/chromium.org/chromedriver/downloads

from __future__ import absolute_import, division, print_function

import sys
import json
import re

import datetime
import time

import urllib

from selenium import webdriver
from selenium.webdriver.support.events import EventFiringWebDriver
from selenium.webdriver.support.events import AbstractEventListener

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup
import json
import yaml
import os
from slackclient import SlackClient
from time import sleep

#FOR REAL USE set this to be True to hide Chrome screen
HEADLESSNESS = True

#defalut value
SLACK_TOKEN = ''
SLACK_USER_ID = ''
SLACK_CHANNEL: ''
SLACK_MENTION: ''

#loading credentials
args = sys.argv
# credentials_mukai.yaml
with open(args[1],"r") as stream:
    try:
        credentials = yaml.load(stream, Loader=yaml.SafeLoader)
        globals().update(credentials)
    except yaml.YAMLError as exc:
        print(exc)

FORMAT = "%Y-%m-%d %H:%M:%S"

def delete_reminder(reminder_id):
    sc = SlackClient(SLACK_TOKEN)
    return sc.api_call(
        "reminders.delete",
        token=SLACK_TOKEN,
        reminder=reminder_id
    )

def post_reminder(text,time):
    sc = SlackClient(SLACK_TOKEN)
    return sc.api_call(
        "reminders.add",
        token=SLACK_TOKEN,
        text=text,
        time=int(time)
        #user=SLACK_USER_ID
    )

# get "HH:MM - HH:MM" string and return a tuple that contains two time objects
def parse_start_end(start_end):

    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d ")
    start, end = start_end.split(" - ")
    start_time = datetime.datetime.strptime(date_str + start, "%Y-%m-%d " + "%H:%M")
    end_time = datetime.datetime.strptime(date_str + end, "%Y-%m-%d " + "%H:%M")

    return (start_time,end_time)


class ScreenshotListener(AbstractEventListener):
    #count for error screenshots
    exception_screenshot_count = 0

    def on_exception(self, exception, driver):
        screenshot_name = "00_exception_{:0>2}.png".format(ScreenshotListener.exception_screenshot_count)
        ScreenshotListener.exception_screenshot_count += 1
        driver.get_screenshot_as_file(screenshot_name)
        print("Screenshot saved as '%s'" % screenshot_name)

def makeDriver(*, headless=True):
    options = Options()
    if(headless):
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,800')
    _driver = webdriver.Chrome(options=options)
    return EventFiringWebDriver(_driver, ScreenshotListener())

def loginDesknets(driver):
    url = DN_URL

    driver.get(url)
    driver.implicitly_wait(10)

    userId_box = driver.find_element_by_name('UserID')
    pass_box = driver.find_element_by_name('_word') 
    userId_box.send_keys(DN_USERNAME)
    pass_box.send_keys(DN_PASSWORD)

    #driver.save_screenshot('0before login.png')
    #print( "saved before login" )

    #login
    driver.find_element_by_id('login-btn').click()

    #elemは特に使わないが、ページが表示されるまで待ちたいため入れている
    elem = driver.find_element_by_css_selector(".portal-cal-body")

    #スケジュール画面遷移    
    driver.find_element_by_css_selector('#portal-content-1 > div.portal-content-titlebar > h3 > a').click()
    sleep(3)
    
    #組織週間画面遷移
    driver.find_element_by_css_selector('#jsch-tab-schweekgrp > a').click()
    sleep(3)
    
    elem = driver.find_element_by_css_selector("#jsch-schweekgrp > form > div.sch-gweek.sch-cal-group-week.jsch-cal-list.jco-print-template.sch-data-view-area > div.sch-gcal-target.me.cal-h-cell.jsch-cal > div.sch-gcal-target-header.me > div")

    #driver.save_screenshot('1after login.png')
    #print( "saved after login" )
    print("URL:" + driver.current_url)
    
    return driver

#スケジュールを取得して[{start:時間, title:タイトル, location:場所}, ...] の形式で返す
def getSchedule(driver):

    nth_calendar_item_selector = DN_SELECTOR + DN_SELECTOR_CL + ' > div:nth-child(%d)'
    nth_duration = DN_SELECTOR + ' > div > div:nth-child(%d) > a > span.cal-term-text'
    size = len(driver.find_elements_by_css_selector( DN_SELECTOR + DN_SELECTOR_CL + ' > div'))
    
    #print( size )
    #print( nth_calendar_item_selector )
    
    driver.implicitly_wait(2)
    calendar_items = []
    for i in range(1, size+1):
        #clicking position which does nothing but closing detail window
        driver.find_element_by_css_selector('#dn-h-search > form > input.searchbox').click()

        #clicking calendar item
        ith_calendar_item_selector = nth_calendar_item_selector % i
        #print(ith_calendar_item_selector)
        driver.find_element_by_css_selector(ith_calendar_item_selector).click()

        #because implicit wait did not cut
        time.sleep(1)

        #detail-title
        title = driver.find_element_by_css_selector('.cal-ref-pop-up-titlebar').text

        try:
            #duration
            ith_duration = nth_duration % i
            duration = driver.find_element_by_css_selector(ith_duration).text
            start_time, end_time = parse_start_end(duration)
        except NoSuchElementException:
            print("one of necessary elements are not found, skipping")
            continue

        #detail-location
        try:
            location1 = driver.find_element_by_css_selector("#cal-ref-pop-up > div.co-baloon-body.jcal-ref-pop-up-frame > table > tbody > tr:nth-child(3) > td").text
        except NoSuchElementException:
            print("location1 is not found")
            location1 = "[blank location]"
        try:
            location2 = driver.find_element_by_css_selector("#cal-ref-pop-up > div.co-baloon-body.jcal-ref-pop-up-frame > table > tbody > tr:nth-child(4) > td").text
        except NoSuchElementException:
            print("location2 is not found")
            location2 = "[blank location]"
        location = "%s %s" % (location1, location2)

        #driver.save_screenshot('2each item_%d.png' % i)
        #print('saved 2each calendar item_%d.png' % i)

        #print("title:%s, start_time:%s, end_time:%s, location:%s" % (title,start_time,end_time,location) )
        calendar_items.append( (title,start_time,end_time,location) )

    driver.implicitly_wait(10)
    return calendar_items

################## main starts here ##################################
if __name__ == "__main__":
    print( "【start】" + SLACK_USER_ID + " " + str(datetime.datetime.now()))
    
    sc = SlackClient(SLACK_TOKEN)

    driver = makeDriver(headless=HEADLESSNESS)
    print( 'driver created' )

    try:

        loginDesknets(driver)

        schedule_items = getSchedule(driver)

    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    finally:
        if HEADLESSNESS:
            driver.quit()

    current_reminders = sc.api_call(
    "reminders.list"
    )
    if not current_reminders.get('ok'):
        print('Slack接続エラー:' +current_reminders.get('error'))

    filtered_reminders = list(filter((lambda x: (x.get('complete_ts') == 0) and x.get('recurring') == False),current_reminders.get('reminders')))
    #print(filtered_reminders)

    #make {time:{title:[id, ...]}} dictionary of current reminders
    text_id_dic = {}
    for reminder in filtered_reminders:
        _time = reminder[u'time']
        _id = reminder[u'id']
        _text = reminder[u'text']

        if _time not in text_id_dic:
            text_id_dic[_time] = {}
        if _text not in text_id_dic[_time]: 
            text_id_dic[_time][_text] = []

        text_id_dic[_time][_text].append(_id)

    #print("current reminders")
    #print(text_id_dic)

    for schedule_item in schedule_items:
        #start_time, end_time, title = schedule_item
        title, start_time, end_time, location = schedule_item

        print("title:%s, start_time:%s, end_time:%s, location:%s" % (title,start_time,end_time,location) )
        message = "%s @%s" % (title, location)

        start_minus_5min = start_time - datetime.timedelta(minutes=5)

        unix_starttime = time.mktime( start_minus_5min.timetuple() )

        #post a reminder iff there are no dupicating reminders
        if((unix_starttime in text_id_dic) and (message in text_id_dic[unix_starttime]) ):
            None
        else:
            print("posting reminder message:", message, " time:", start_minus_5min)
            response = post_reminder(message,unix_starttime)
            print(response)

        sc.api_call(
        "chat.postMessage",
        channel=SLACK_CHANNEL,
        text=SLACK_MENTION+message,
        username="desknet's NEO スケジュール連携",
        user=SLACK_USER_ID
        )
    print( "【end  】" + SLACK_USER_ID + " " + str(datetime.datetime.now()))