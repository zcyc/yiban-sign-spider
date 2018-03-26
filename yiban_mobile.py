#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import random
import json
import logging
import threading
import time
from user_agents import parse

logging.getLogger("requests").setLevel(logging.WARNING)

logging.basicConfig(filename='mobile.log', filemode='w', level=logging.INFO, format='[%(levelname)s] (%(threadName)-10s) %(message)s',)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s'))
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)


user_agents = [
  'Mozilla/5.0 (Linux; Android 6.0.1; SM-G9280 Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/49.0.2623.91 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 5.1; MX5 Build/LMY47I) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/49.0.2623.91 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 5.1; OPPO R9tm Build/LMY47I) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/49.0.2623.91 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 7.0; KNT-UL10 Build/HUAWEIKNT-UL10) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/49.0.2623.91 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 6.0.1; MI 5s Plus Build/MXB48T) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/49.0.2623.91 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 7.0; VTR-AL00 Build/HUAWEIVTR-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/49.0.2623.91 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 6.0.1; vivo X9Plus Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/49.0.2623.91 Mobile Safari/537.36',
]


def makeSomeBoom(username, password):
  #Let go
  logging.debug('Job Starting!')

  #Pre Login Info
  pre_headers = {
    'User-Agent': random.choice(user_agents),
    'Authorization': 'Bearer',
    'AppVersion': '4.5.4'
  }

  pre_payload = {
    'account': username,
    'passwd': password,
    'ct': '2',
    'app': '1',
    'v': pre_headers['AppVersion'],
    'apn': 'wifi',
    'identify': random.randint(1, 99999),
    'sig': '',
    'token': '',
    'device': str(parse(pre_headers['User-Agent'])).split(' / ')[0],
    'sversion': '23'
  }

  try:
    PreloginData = requests.get("https://mobile.yiban.cn/api/v2/passport/login", headers=pre_headers, params=pre_payload).json()
  except:
    logging.error('Unknow error excepted! May password error!')
    return
  
  if PreloginData['response'] != '100':
    logging.error('Pre Login Error: ' + PreloginData['message'])
    return
  else:
    logging.info('Pre Login Succeed!')
  
  access_token = PreloginData['data']['access_token']
  
  
  #Start to checkin
  checkin_headers = {
    'User-Agent': pre_headers['User-Agent'],
    'Authorization': 'Bearer ' + access_token,
    'AppVersion': pre_payload['v'],
    'loginToken': access_token
  }
  
  checkin_payload = {
    'access_token': access_token,
  }


  try:
    checkinData = requests.get("https://mobile.yiban.cn/api/v3/checkin/question", headers=checkin_headers, params=checkin_payload).json()
  except:
    logging.error('Unknow error excepted! Cannot Pre Checkin!')
    return

  if checkinData['data']['isChecked']:
    logging.warning('User: ' + pre_payload['account'] + ' already checked in!')
  else:
    if checkinData['data']['has_survey']:
      try:
        result = requests.post("http://mobile.yiban.cn/api/v3/checkin/answer?access_token="+access_token+"&optionId="+random.choice(checkinData['data']['survey']['question']['option'])['id']+"&feeds=1", headers=checkin_headers).json()
      except:
        logging.error('Unknow error excepted! Cannot Checkin!')
        return

      if result['response'] != 100:
        logging.warning("CheckIn : " + result['message'])
      else:
        logging.info("CheckIn Successful!")
        try:
          requests.post("http://mobile.yiban.cn/api/v3/feeds?access_token="+access_token+"&content=%25E6%2588%2591%25E5%259C%25A8%25E6%2598%2593%25E7%258F%25AD%25E7%25AD%25BE%25E5%2588%25B0%25EF%25BC%258C%25E7%25BD%2591%25E8%2596%25AA%25E5%25BF%25AB%25E5%2588%25B0%25E7%25A2%2597%25E9%2587%258C%25E6%259D%25A5%257E&visibleScope=0&kind=2&to_userids=&address=&artwork=0&lat=0.0&lng=0.0")
        except:
          logging.error('Unknow error excepted! Cannot add feed!')

    else:
      logging.info("Today dont have survey!")
  
 #Let Logout
  try:
    logout = requests.get("http://mobile.yiban.cn/api/v1/passport/logout?access_token="+access_token).json()
  except:
    logging.error('Unknow error excepted! Cannot Logout!')
    return

  if logout['response'] != '100':
    logging.error("Logout Error: " + logout['message'])
  else:
    logging.info("Logout Successful!")

  #OK,we have done the job
  logging.debug('Job Done')

def chunkWorker(chunk, chunkNow, chunkAll):
  for line in chunk:
    myline = line.replace('"', '').split(',')
    if len(myline) != 7:
      logging.error("User: "+myline[0]+" not found!")
    else:
      user = myline[2]
      passwd = myline[3]
      myThread = threading.Thread(name='No.'+str(chunk.index(line)+1)+' '+str(chunkNow)+'-'+str(chunkAll)+' '+user, target=makeSomeBoom, args=(user, passwd, ))
      myThread.start()
      time.sleep(0.1)

if __name__ == '__main__':
  userList='./cha_kedou100_co.csv'
  with open(userList) as myUser:
    lines = myUser.readlines()
    # limit jobs
    lines = lines[random.randint(987,1234):]
    chunkSize = 30
    chunkedLines = [lines[i:i + chunkSize] for i in xrange(0, len(lines), chunkSize)]
    delay = 1
    for chunk in chunkedLines:
      logging.info('Working on Chunk '+str(chunkedLines.index(chunk) + 1)+' OF '+str(len(chunkedLines)))
      chunkWorker(chunk, chunkedLines.index(chunk)+1, len(chunkedLines))
      logging.info("Delaying for "+str(delay)+"s")
      time.sleep(delay)
