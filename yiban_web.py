#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import random
import logging
import threading
import time
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from base64 import b64encode, b64decode
from bs4 import BeautifulSoup, element

logging.getLogger("requests").setLevel(logging.WARNING)

logging.basicConfig(filename='web.log', filemode='w', level=logging.INFO, format='[%(levelname)s] (%(threadName)-10s) %(message)s',)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s'))
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)


user_agents = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
  'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60'
]


def makeSomeBoom(username, password):
  #Let go
  logging.debug('Job Starting!')

  #We need some cookies!
  headers = {
    'User-Agent': random.choice(user_agents),
  }

  init = requests.get('https://www.yiban.cn/login', headers=headers)
  html = BeautifulSoup(init.text, "html.parser")
  keys = html.find(id="login-pr")["data-keys"].strip()
  keys = str(''.join(keys.split('\n')[1:-1]))
  keysTime = str(html.find(id="login-pr")["data-keys-time"])

  keyPub = RSA.importKey(b64decode(keys))
  cipher = Cipher_pkcs1_v1_5.new(keyPub)

  #Let login
  payload = {
    'account': username,
    'password': b64encode(cipher.encrypt(password)),
    'keysTime': keysTime,
    'captcha': ''
  }

  try:
    login = requests.post('https://www.yiban.cn/login/doLoginAjax', data=payload, cookies=init.cookies, headers=headers).json()
#712
    if login['code'] == 712:
      makeSomeBoom(username, password)
      return
  except:
    logging.error('Unknow error excepted! May password error!')
    return
  
  if login['code'] != 200:
    logging.error(login['code'])
    logging.error('Login Error: ' + login['message'])
    return
  else:
    logging.info('Login Succeed!')

  #Let's get some info
  try:
    preCheckin = requests.post('http://www.yiban.cn/ajax/checkin/checkin', headers=headers, cookies=init.cookies).json()
  except:
    logging.error('Unknow error excepted! Cannot pre checkin!')
    return

  if preCheckin['code'] != 200:
    logging.warning('User '+username+' '+ preCheckin['message'])
    return
  else:
    logging.info('Pre Checkin Succeed!')

  if preCheckin['data']['has_survey']:
    soup = BeautifulSoup(preCheckin['data']['survey'], "html.parser")
    dataValue = list({tmp['data-value'] for tmp in soup.find_all('i', {'data-input' : '0'})})
    payload = {
      'optionid[]': random.choice(dataValue),
      'input': ''
    }

    #Let CheckIN
    try:
      Checkin = requests.post('http://www.yiban.cn/ajax/checkin/answer', headers=headers, cookies=init.cookies, data=payload).json()
    except:
      logging.error('Unknow error excepted! Cannot Checkin!')
      return

    if Checkin['code'] != 200:
      logging.warning('Checkin fail: ' + preCheckin['data']['subMessage'])
      return
    else:
      logging.info('Checkin Succeed!')
  else:
    logging.info('Today dont have survey!')

  #POST SOME DATA
  payload = {
    'content': '我在易班签到，网薪快到碗里来~',
    'privacy': '0',
    'dom': '.js-submit'
  }

  try:
    requests.post('http://www.yiban.cn/feed/add', headers=headers, cookies=init.cookies, data=payload)
  except:
    logging.error('Cannot add feed!')
    return


  #We should logout
  try:
    requests.get('https://www.yiban.cn/logout', headers=headers, cookies=init.cookies)
  except:
    logging.error('Unknow error excepted! Cannot Logout!')
    return

  #OK,we have done the job
  logging.debug('Job Done')


def chunkWorker(chunk, chunkNow, chunkAll):
  for line in chunk:
    myline = line.replace('"', '').split(',')
    if len(myline) != 7:
      logging.error("User: "+myline[2]+" not found!")
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
    lines = lines[:random.randint(987,1234)]
    chunkSize = 30
    chunkedLines = [lines[i:i + chunkSize] for i in xrange(0, len(lines), chunkSize)]
    delay = 0.3
    for chunk in chunkedLines:
      logging.info('Working on Chunk '+str(chunkedLines.index(chunk) + 1)+' OF '+str(len(chunkedLines)))
      chunkWorker(chunk, chunkedLines.index(chunk)+1, len(chunkedLines))
      logging.info("Delaying for "+str(delay)+"s")
      time.sleep(delay)
