from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
  MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage,
  ImageSendMessage, AudioMessage, ButtonsTemplate, MessageTemplateAction,
  PostbackEvent, PostbackTemplateAction, MessageAction, CarouselTemplate,
  CarouselColumn, PostbackAction, URIAction)
from IPython.display import display, HTML

import os
import uuid
import re
import random
import json  #json
import datetime  #轉換時間戳記
import codecs  #ASCII
import pandas as pd
import pytz  #時區轉換
import numpy


from datetime import datetime

from src.models import OpenAIModel
from src.memory import Memory
from src.logger import logger
from src.storage import Storage
from src.utils import get_role_and_content

load_dotenv('.env')

# 讀入總題庫
with open("Questions.json", encoding='utf8') as f:
  questions_dic = json.loads(f.read())
#改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!
today_date='0508'
dirpath_sturesp_allData = f"sturesp/allData/{today_date}/"
#改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!改日期!
# 讀入總題庫

questions_resp_stast = {}
for i in questions_dic.keys():
  questions_resp_stast[i] = {
    'ans_1st':{
      'A':[],'B':[],'C':[],'D':[]
    },
    'ans_2nd':{
      'A':[],'B':[],'C':[],'D':[]
    },
    'ans_3rd':{
      'A':[],'B':[],'C':[],'D':[]
    },
    'ans_4th':{
      'A':[],'B':[],'C':[],'D':[]
    }
  }


app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
storage = Storage('db.json')
#新立的變數
SM = 'You are an elementary school teacher.Reply in a way that elementary school students can understand.Reply should be short and precise.1平方公里=100公頃。1公頃=100公畝。1公畝=100平方公尺。1平方公尺=10000平方公分。1公噸=1000公斤。1公斤=1000公克。1公里=1000公尺。1公尺=100公分。40%off是打六折的意思。'
#
memory = Memory(system_message=os.getenv('SYSTEM_MESSAGE'),
                memory_message_count=2)
model_management = {}
api_keys = {}
api_key = os.getenv('OPENAI_API')
#print(api_key)

@app.route("/callback", methods=['POST'])
def callback():
  signature = request.headers['X-Line-Signature']
  body = request.get_data(as_text=True)
  app.logger.info("Request body: " + body)
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    print(
      "Invalid signature. Please check your channel access token/channel secret."
    )
    abort(400)
  return 'OK'


@handler.add(MessageEvent, message=TextMessage)
#收到訊息
def handle_text_message(event):
  user_id = event.source.user_id
  text = event.message.text.strip()
  logger.info(f'{user_id}: {text}')
  global api_keys, api_key
  api_keys[user_id] = api_key  #直接註冊

  #抓時間
  utc_time = datetime.datetime.utcnow()
  utc_zone = pytz.timezone('UTC')
  tw_zone = pytz.timezone('Asia/Taipei')
  utc_dt = utc_zone.localize(utc_time)
  tw_dt = utc_dt.astimezone(tw_zone)
  time = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
  #抓時間

  #global ran_q
  msg = []
  actions = []

  #定義存入學生回應訊息(ID、時間、訊息)
  def stuResp(user_id, time, text, sys):
    os.makedirs("sturesp/allresp", exist_ok=True)
    with open(f"sturesp/allresp/{user_id}.txt", mode="a+",
              encoding="utf8") as resp:
      tg_text = {"ID": f"{user_id}{sys}", "時間": time, "訊息": text}
      resp.write(str(tg_text) + '\n')

  #定義 存入學生回應訊息(ID、時間、訊息)

  #存個人發送的訊息
  stuResp(user_id, time, text, "")
  #存個人發送的訊息

  #確認學生總資料是否存在
  #print("102 確認學生總資料是否存在")
  if not os.path.exists(f"{dirpath_sturesp_allData}{user_id}.json"):
    #print("\t檔案不存在")
    exist_file = open(f"{dirpath_sturesp_allData}{user_id}.json", mode="a")
    #print("\ta檔案")
    json.dump(
      {
        f"{user_id}": {
          "stu_okQnum": [],
          "stu_ranQ": "",
          "FQnum_list": [],
          "count_okQ": 0,
          "stu_score": 0
        }
      }, exist_file)
    exist_file.close()
  #確認學生總資料是否存在

  #定義 寫入新資料
  def revise_allData(user_id,
                     stu_okQnum=None,
                     stu_ranQ=None,
                     FQnum_list=None,
                     count_okQ=None,
                     stu_score=None):
    revise_new_allData = {}
    #print("126 寫入新資料")
    #print("\tr檔")
    rv_allData_file = open(f"{dirpath_sturesp_allData}{user_id}.json",
                           mode="r")
    #print("\tload檔")
    rAllData = json.load(rv_allData_file)
    if stu_okQnum != None:
      rAllData[user_id]["stu_okQnum"].append(stu_okQnum.replace('"', ''))
      #print("\tstu_okQnum:", stu_okQnum.replace('"', ''))
    if stu_ranQ != None:
      rAllData[user_id]["stu_ranQ"] = stu_ranQ.replace('"', '')  #OK
      #print("\tstu_ranQ:", stu_ranQ.replace('"', ''))
    if FQnum_list != None:
      rAllData[user_id]["FQnum_list"].append(FQnum_list.replace('"', ''))
      #print("\tFQnum_list:", FQnum_list.replace('"', ''))
    if count_okQ != None:
      rAllData[user_id]["count_okQ"] = count_okQ  #.replace('"', '')
      #print("\tcount_okQ:", count_okQ.replace('"', ''))
    if stu_score != None:
      rAllData[user_id]["stu_score"] = stu_score  #.replace('"', '')
      #print("\tstu_score寫入成功:", rAllData[user_id]["stu_score"])
    #print("\t覆寫字典revise_new_allData")
    revise_new_allData = rAllData
    rv_allData_file.close()
    #print("146 回傳字典revise_new_allData長這樣:",revise_new_allData)
    return revise_new_allData

  #定義 寫入新資料

  #定義 寫入更新資料
  def write_allData(new_allData):
    #print("152 w檔案")
    write_allData_file = open(f"{dirpath_sturesp_allData}{user_id}.json",
                              mode="w")
    #print("\t傳入的長這樣:",new_allData)
    new_allData[user_id]["stu_okQnum"] = list(
      set(new_allData[user_id]["stu_okQnum"]))
    #print("\t更改的長這樣:",new_allData)
    json.dump(new_allData, write_allData_file)
    #print("156 w檔案成功")
    write_allData_file.close()

  #定義 寫入更新資料

  #定義 更新資料(要更新的資料)
  def rvStuData(user_id,
                stu_okQnum=None,
                stu_ranQ=None,
                FQnum_list=None,
                count_okQ=None,
                stu_score=None):
    #更新資料
    #print("168呼叫revise_allData跟write_allData")
    write_allData(
      revise_allData(user_id, stu_okQnum, stu_ranQ, FQnum_list, count_okQ,
                     stu_score))
    #print("171呼叫revise_allData跟write_allData成功")

  #定義 更新資料

  #定義 抓取資料
  def get_allData(user_id,
                  stu_okQnum=None,
                  stu_ranQ=None,
                  FQnum_list=None,
                  count_okQ=None,
                  stu_score=None):
    #print("181 抓取檔案資料get_allData")
    #print("\tr檔案")
    get_allData_file = open(f"{dirpath_sturesp_allData}{user_id}.json",
                            mode="r")
    #print("\tload檔案")
    rAllData = json.load(get_allData_file)
    #print("\t寫入字典")
    get_new_allData = {}
    if stu_okQnum != None:
      get_new_allData["stu_okQnum"] = rAllData[user_id]["stu_okQnum"]
    if stu_ranQ != None:
      get_new_allData["stu_ranQ"] = rAllData[user_id]["stu_ranQ"]
    if FQnum_list != None:
      get_new_allData["FQnum_list"] = rAllData[user_id]["FQnum_list"]
    if count_okQ != None:
      get_new_allData["count_okQ"] = rAllData[user_id]["count_okQ"]
    if stu_score != None:
      get_new_allData["stu_score"] = rAllData[user_id]["stu_score"]
    get_allData_file.close()
    #print("197 抓取檔案資料成功，回傳字典get_new_allData長這樣:", get_new_allData)
    return get_new_allData

  #定義 抓取資料

  if text.startswith('「題目」'):
    #隨機抽題目
    #print("204 隨機抽題號")
    global numsQ, ran_numsQ
    numsQ = []
    #for i in range(len(questions_dic)):
    #  numsQ.append(i + 1)  #創抽取題號的list [1, 2, 3, .....]
    for i in questions_dic:
      numsQ.append(i)  #創抽取題號的list [1, 2, 3, .....]
    ran_numsQ = random.choice(numsQ)  #隨機抽題號

    #print("\t呼叫rvStuData")
    #rvStuData(user_id, stu_ranQ="q" + str(ran_numsQ))  #更新stu_ranQ
    rvStuData(user_id, stu_ranQ=ran_numsQ)  #更新stu_ranQ
    #print("212抽對應題目進stu_nowq_dic")
    stu_nowq_dic = questions_dic[get_allData(user_id,
                                             stu_ranQ=1)["stu_ranQ"]]  #抽對應題目
    #隨機抽題目

    #print("\t判斷答題次數(1答完)")
    #print("\t判斷答題次數(2沒有題目回答正確)")
    #print("\t判斷答題次數(3有題目沒答完)")
    len_questions_dic = len(questions_dic)
    get_count_okQ = int(get_allData(user_id, count_okQ=1)["count_okQ"])
    if get_count_okQ >= len_questions_dic:  #若所有題目都回答正確
      #print("222恭喜你~已經完成今天的題目囉！")
      msg_text = f"恭喜你~已經完成今天的題目囉！({today_date}) 你的努力得到了: " + get_allData(
        user_id, stu_score=1)["stu_score"] + " 分!"
      msg = TextSendMessage(text=msg_text)
      stuResp(user_id, time, msg_text, "(系統)")
    elif get_count_okQ == 0:  #沒有題目回答正確 (回答正確的題目數=0)
      #print("226回答正確的題目數=0")
      #print(get_allData(user_id, stu_ranQ=1)["stu_ranQ"])
      stu_nowq_dic = questions_dic[get_allData(user_id,
                                               stu_ranQ=1)["stu_ranQ"]]
      get_q_title = stu_nowq_dic['q_title']
      for option in ['A', 'B', 'C', 'D']:
        action = PostbackTemplateAction(
          label=f"({option}) {stu_nowq_dic['options'][option]}",
          text=f"({option}) {stu_nowq_dic['options'][option]}",
          data=f"{option}&{stu_nowq_dic['options'][option]}")
        actions.append(action)
      template = ButtonsTemplate(
        title=get_q_title + f" (進度:{get_count_okQ+1}/{len_questions_dic})",
        text=stu_nowq_dic['q'],
        actions=actions)
      message = TemplateSendMessage(alt_text='題目：' + str(stu_nowq_dic['q']) +
                                    '\n選項：' + str(stu_nowq_dic['options']),
                                    template=template)
      msg.append(message)
      stuResp(user_id, time,
              f"題目：{stu_nowq_dic['q']}選項：{str(stu_nowq_dic['options'])}",
              "(系統)")
    else:  #有題目沒答完
      while True:
        #print("248 看是否重複抽題")
        if get_allData(user_id, stu_ranQ=1)["stu_ranQ"] in get_allData(
            user_id, stu_okQnum=1)["stu_okQnum"]:
          #print("250 重新抽題")
          ran_numsQ = random.choice(numsQ)
          #
          rvStuData(user_id, stu_ranQ=ran_numsQ)
          stu_nowq_dic = questions_dic[get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"]]
        else:
          break
      stu_nowq_dic = questions_dic[get_allData(user_id,
                                               stu_ranQ=1)["stu_ranQ"]]
      get_q_title = stu_nowq_dic['q_title']
      for option in ['A', 'B', 'C', 'D']:
        action = PostbackTemplateAction(
          label=f"({option}) {stu_nowq_dic['options'][option]}",
          text=f"({option}) {stu_nowq_dic['options'][option]}",
          data=f"{option}&{stu_nowq_dic['options'][option]}")
        actions.append(action)
      template = ButtonsTemplate(
        title=get_q_title + f" (進度:{get_count_okQ+1}/{len_questions_dic})",
        text=stu_nowq_dic['q'],
        actions=actions)
      message = TemplateSendMessage(alt_text='題目：' + str(stu_nowq_dic['q']) +
                                    '\n選項：' + str(stu_nowq_dic['options']),
                                    template=template)
      msg.append(message)
      stuResp(user_id, time,
              f"題目：{stu_nowq_dic['q']}選項：{str(stu_nowq_dic['options'])}",
              "(系統)")
  #調用答案
  elif text.startswith('(A) '):
    #print("278判斷答案")
    stu_nowq_dic = questions_dic[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]
    if 'A' == stu_nowq_dic['a']:
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      if count_FQnum_list == 0:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['A'].append(user_id)
        text_score = '太好了!第一次就答對了!(+3分)'
        score = 3
      elif count_FQnum_list == 1:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      elif count_FQnum_list == 2:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      else:
        text_score = '答對了!(+1分)'
        score = 1
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
      #print("283 答對呼叫rvStuData寫stu_score")
      #print("\tscore:+", score)
      if get_allData(user_id, stu_ranQ=1)["stu_ranQ"] not in get_allData(
          user_id, stu_okQnum=1)["stu_okQnum"]:
        rvStuData(user_id,
                  stu_score=json.dumps(
                    int(get_allData(user_id, stu_score=1)["stu_score"]) +
                    score))
        #print("\t", int(get_allData(user_id, stu_score=1)["stu_score"]))
      #print("\t再一次呼叫rvStuData寫stu_okQnum")
      rvStuData(user_id,
                stu_okQnum=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      #print("\t再一次呼叫rvStuData寫FQnum_list")
      rvStuData(user_id,
                count_okQ=json.dumps(
                  len(get_allData(user_id, stu_okQnum=1)["stu_okQnum"])))
      #print("成功!")
    else:
      #print("\tdumps進FQnum_list")
      rvStuData(user_id,
                FQnum_list=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      #print('\t錯了:', count_FQnum_list, '次')
      if count_FQnum_list == 1:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['A'].append(user_id)
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      if count_FQnum_list == 2:
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      elif count_FQnum_list == 3:
        text_score = '或許你可以尋求幫助...' + '(' + str(stu_nowq_dic['tip']) + ')'
      else:
        text_score = '別灰心!訂正好後再做答吧!' + '(' + str(stu_nowq_dic['explain']) + ')'
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
  elif text.startswith('(B) '):  #換成一個變數，調出上一題的選項答案，以及詳解
    #print("278判斷答案")
    stu_nowq_dic = questions_dic[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]
    if 'B' == stu_nowq_dic['a']:
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      if count_FQnum_list == 0:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['B'].append(user_id)
        text_score = '太好了!第一次就答對了!(+3分)'
        score = 3
      elif count_FQnum_list == 1:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      elif count_FQnum_list == 2:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      else:
        text_score = '答對了!(+1分)'
        score = 1
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
      #print("283 答對呼叫rvStuData寫stu_score")
      #print("\tscore:+", score)
      if get_allData(user_id, stu_ranQ=1)["stu_ranQ"] not in get_allData(
          user_id, stu_okQnum=1)["stu_okQnum"]:
        rvStuData(user_id,
                  stu_score=json.dumps(
                    int(get_allData(user_id, stu_score=1)["stu_score"]) +
                    score))
        #print("\t", int(get_allData(user_id, stu_score=1)["stu_score"]))
      #print("\t再一次呼叫rvStuData寫stu_okQnum")
      rvStuData(user_id,
                stu_okQnum=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      #print("\t再一次呼叫rvStuData寫FQnum_list")
      rvStuData(user_id,
                count_okQ=json.dumps(
                  len(get_allData(user_id, stu_okQnum=1)["stu_okQnum"])))
      #print("成功!")
    else:
      #print("\tdumps進FQnum_list")
      rvStuData(user_id,
                FQnum_list=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      #print('\t錯了:', count_FQnum_list, '次')
      if count_FQnum_list == 1:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['B'].append(user_id)
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      if count_FQnum_list == 2:
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      elif count_FQnum_list == 3:
        text_score = '或許你可以尋求幫助...' + '(' + str(stu_nowq_dic['tip']) + ')'
      else:
        text_score = '別灰心!訂正好後再做答吧!' + '(' + str(stu_nowq_dic['explain']) + ')'
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
  elif text.startswith('(C) '):  #換成一個變數，調出上一題的選項答案，以及詳解
    #print("278判斷答案")
    stu_nowq_dic = questions_dic[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]
    if 'C' == stu_nowq_dic['a']:
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      if count_FQnum_list == 0:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['C'].append(user_id)
        text_score = '太好了!第一次就答對了!(+3分)'
        score = 3
      elif count_FQnum_list == 1:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      elif count_FQnum_list == 2:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      else:
        text_score = '答對了!(+1分)'
        score = 1
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
      #print("283 答對呼叫rvStuData寫stu_score")
      #print("\tscore:+", score)
      if get_allData(user_id, stu_ranQ=1)["stu_ranQ"] not in get_allData(
          user_id, stu_okQnum=1)["stu_okQnum"]:
        rvStuData(user_id,
                  stu_score=json.dumps(
                    int(get_allData(user_id, stu_score=1)["stu_score"]) +
                    score))
        #print("\t", int(get_allData(user_id, stu_score=1)["stu_score"]))
      #print("\t再一次呼叫rvStuData寫stu_okQnum")
      rvStuData(user_id,
                stu_okQnum=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      #print("\t再一次呼叫rvStuData寫FQnum_list")
      rvStuData(user_id,
                count_okQ=json.dumps(
                  len(get_allData(user_id, stu_okQnum=1)["stu_okQnum"])))
      #print("成功!")
    else:
      #print("\tdumps進FQnum_list")
      rvStuData(user_id,
                FQnum_list=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      #print('\t錯了:', count_FQnum_list, '次')
      if count_FQnum_list == 1:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['C'].append(user_id)
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      if count_FQnum_list == 2:
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      elif count_FQnum_list == 3:
        text_score = '或許你可以尋求幫助...' + '(' + str(stu_nowq_dic['tip']) + ')'
      else:
        text_score = '別灰心!訂正好後再做答吧!' + '(' + str(stu_nowq_dic['explain']) + ')'
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
  elif text.startswith('(D) '):  #換成一個變數，調出上一題的選項答案，以及詳解
    #print("278判斷答案")
    stu_nowq_dic = questions_dic[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]
    if 'D' == stu_nowq_dic['a']:
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      if count_FQnum_list == 0:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['D'].append(user_id)
        text_score = '太好了!第一次就答對了!(+3分)'
        score = 3
      elif count_FQnum_list == 1:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      elif count_FQnum_list == 2:
        text_score = '訂正後答對了!(+2分)'
        score = 2
      else:
        text_score = '答對了!(+1分)'
        score = 1
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
      #print("283 答對呼叫rvStuData寫stu_score")
      #print("\tscore:+", score)
      if get_allData(user_id, stu_ranQ=1)["stu_ranQ"] not in get_allData(
          user_id, stu_okQnum=1)["stu_okQnum"]:
        rvStuData(user_id,
                  stu_score=json.dumps(
                    int(get_allData(user_id, stu_score=1)["stu_score"]) +
                    score))
        #print("\t", int(get_allData(user_id, stu_score=1)["stu_score"]))
      #print("\t再一次呼叫rvStuData寫stu_okQnum")
      rvStuData(user_id,
                stu_okQnum=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      #print("\t再一次呼叫rvStuData寫FQnum_list")
      rvStuData(user_id,
                count_okQ=json.dumps(
                  len(get_allData(user_id, stu_okQnum=1)["stu_okQnum"])))
      #print("成功!")
    else:
      #print("\tdumps進FQnum_list")
      rvStuData(user_id,
                FQnum_list=json.dumps(
                  str(get_allData(user_id,
                                  stu_ranQ=1)["stu_ranQ"]).replace('"', '')))
      count_FQnum_list = get_allData(user_id,
                                     FQnum_list=1)["FQnum_list"].count(
                                       get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"])
      #print('\t錯了:', count_FQnum_list, '次')
      if count_FQnum_list == 1:
        questions_resp_stast[get_allData(user_id, stu_ranQ=1)["stu_ranQ"]]['ans_1st']['D'].append(user_id)
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      if count_FQnum_list == 2:
        text_score = '答錯囉!冷靜檢查後再回答吧!'
      elif count_FQnum_list == 3:
        text_score = '或許你可以尋求幫助...' + '(' + str(stu_nowq_dic['tip']) + ')'
      else:
        text_score = '別灰心!訂正好後再做答吧!' + '(' + str(stu_nowq_dic['explain']) + ')'
      msg = TextSendMessage(text=text_score)
      stuResp(user_id, time, text_score, "(系統)")
  #調用答案
  else:
    #判讀文字前綴
    try:
      if text.startswith('「說明」'):
        msg = TextSendMessage(text="""❗注意❗
1. 選項按了之後就會送出囉！
2. 在越少次數內答對，就可以得到越多分喔！
3. 答錯沒關係~訂正之後再想想看就好囉！

🔻使用說明🔻
按下圖片就可以使用功能囉！
📋「說明」：使用說明
🎞️「8-1 教學影片」：和8-1課本例題配合的教學影片
🎞️「8-2 教學影片」：和8-2課本例題配合的教學影片
✏️「題目」：回家作業

如果有想更了解的地方，也可以直接向機器人問問題喔！""")
        #存系統發送的訊息
        stuResp(user_id, time, "說明", "(系統)")
        print('(系統:', '說明', ')')
        #存系統發送的訊息
      elif text.startswith('「清除」'):
        memory.remove(user_id)
        msg = TextSendMessage(text='歷史訊息清除成功')
      elif text.startswith('「影片8-1」'):
        msg = TemplateSendMessage(
          #text="""還沒有資源喔~\nhttps://youtu.be/MIR5zIpWBH0""")
          alt_text='CarouselTemplate',
          template=CarouselTemplate(columns=[
            CarouselColumn(
              thumbnail_image_url=
              'https://1.bp.blogspot.com/-ewJgNRP7M6w/X4aVa5VK2LI/AAAAAAABbuA/IXWqMxGm2dgQcbgLKLrBKOFkc71CN76WwCNcBGAsYHQ/s400/animal_chara_mogura_hakase.png',
              title='1.課前暖身',
              text='複習先前學習過的單位，知道公克與公斤的單位換算。',
              actions=[
                #MessageAction(label='hello', text='hello'),
                URIAction(
                  label='生活中的大單位',
                  uri=
                  'https://www.youtube.com/watch?v=a4336YvNTes&list=PLp2Y5q36tB-Pu-aPLyaEdEBYfgRGMxcaQ'
                )
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://2.bp.blogspot.com/-kTwb6ciWUXw/UkJMufV9M1I/AAAAAAAAYSY/ccltLBGRj0M/s400/cooking_hakari.png',
              title='2.數學課本五下8-1節 P99 例題一',
              text='練習公噸與公斤換成公斤。',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-1節 P99 例題一',
                          uri='https://www.youtube.com/watch?v=rMNUy8CdXA8')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://2.bp.blogspot.com/-kTwb6ciWUXw/UkJMufV9M1I/AAAAAAAAYSY/ccltLBGRj0M/s400/cooking_hakari.png',
              title='3.數學課本五下8-1節 P100 例題三',
              text='公噸和公斤為單位的加減法計算',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-1節 P100 例題三',
                          uri='https://www.youtube.com/watch?v=O1u5pVeA4Sc')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://2.bp.blogspot.com/-kTwb6ciWUXw/UkJMufV9M1I/AAAAAAAAYSY/ccltLBGRj0M/s400/cooking_hakari.png',
              title='4.數學課本五下8-1節 P100 例題四',
              text='公噸和公斤為單位的乘法計算',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-1節 P100 例題四',
                          uri='https://www.youtube.com/watch?v=QNUaCIZ4ptQ')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://2.bp.blogspot.com/-kTwb6ciWUXw/UkJMufV9M1I/AAAAAAAAYSY/ccltLBGRj0M/s400/cooking_hakari.png',
              title='5.數學課本五下8-1節 P101 例題五',
              text='用乘法解決以公噸為單位的應用題',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-1節 P101 例題五',
                          uri='https://www.youtube.com/watch?v=RFXcmYwLXrg')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://2.bp.blogspot.com/-kTwb6ciWUXw/UkJMufV9M1I/AAAAAAAAYSY/ccltLBGRj0M/s400/cooking_hakari.png',
              title='6.數學課本五下8-1節 P101 例題六',
              text='利用公噸和公斤的關係，解決換算和除法應用問題 (1)',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-1節 P101 例題六',
                          uri='https://www.youtube.com/watch?v=NcTQHLoxSV8')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://2.bp.blogspot.com/-kTwb6ciWUXw/UkJMufV9M1I/AAAAAAAAYSY/ccltLBGRj0M/s400/cooking_hakari.png',
              title='7.數學課本五下8-1節 P101 例題七',
              text='利用公噸和公斤的關係，解決換算和除法應用問題 (2)',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-1節 P101 例題七',
                          uri='https://www.youtube.com/watch?v=TKx7C6O8LR8')
              ])
          ]))
        #存系統發送的訊息
        stuResp(user_id, time, "影片", "(系統)")
        #print('(系統:', '影片', ')')
        #存系統發送的訊息
      elif text.startswith('「影片8-2」'):
        msg = TemplateSendMessage(
          #text="""還沒有資源喔~\nhttps://youtu.be/MIR5zIpWBH0""")
          alt_text='CarouselTemplate',
          template=CarouselTemplate(columns=[
            CarouselColumn(
              thumbnail_image_url=
              'https://3.bp.blogspot.com/-2b6-5lci0ww/Vt_uCLRxs9I/AAAAAAAA4sQ/O2xyscr4u_U/s400/tensai_boy.png',
              title='1.數學課本五下8-2節 P102 例題一',
              text='平方公尺換算成公畝與平方公尺',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-2節 P102 例題一',
                          uri='https://www.youtube.com/watch?v=lN8WSY5bS3M')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://3.bp.blogspot.com/-2b6-5lci0ww/Vt_uCLRxs9I/AAAAAAAA4sQ/O2xyscr4u_U/s400/tensai_boy.png',
              title='2.數學課本五下8-2節 P104 例題四',
              text='平方公里、公頃、公畝與平方公尺的換算',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-2節 P104 例題四',
                          uri='https://www.youtube.com/watch?v=a4MXW8D5gxc')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://3.bp.blogspot.com/-2b6-5lci0ww/Vt_uCLRxs9I/AAAAAAAA4sQ/O2xyscr4u_U/s400/tensai_boy.png',
              title='3.數學課本五下8-2節 P105 例題五',
              text='公頃和公畝為單位的加減法計算',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-2節 P105 例題五',
                          uri='https://www.youtube.com/watch?v=S6iW8LxBp-k')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://3.bp.blogspot.com/-2b6-5lci0ww/Vt_uCLRxs9I/AAAAAAAA4sQ/O2xyscr4u_U/s400/tensai_boy.png',
              title='4.數學課本五下8-2節 P105 例題六',
              text='公頃和公畝為單位的乘法計算',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-2節 P105 例題六',
                          uri='https://www.youtube.com/watch?v=-ayRTC1eh0I')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://3.bp.blogspot.com/-2b6-5lci0ww/Vt_uCLRxs9I/AAAAAAAA4sQ/O2xyscr4u_U/s400/tensai_boy.png',
              title='5.數學課本五下8-2節 P106 例題七',
              text='利用公畝和平方公尺的關係，解決換算和除法應用問題',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-2節 P106 例題七',
                          uri='https://www.youtube.com/watch?v=SpU8FWvp_rY')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://3.bp.blogspot.com/-2b6-5lci0ww/Vt_uCLRxs9I/AAAAAAAA4sQ/O2xyscr4u_U/s400/tensai_boy.png',
              title='6.數學課本五下8-2節 P106 例題八',
              text='利用公頃和公畝的關係，解決換算和除法應用問題',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-2節 P106 例題八',
                          uri='https://www.youtube.com/watch?v=c2VEj_vRN-M')
              ]),
            CarouselColumn(
              thumbnail_image_url=
              'https://3.bp.blogspot.com/-2b6-5lci0ww/Vt_uCLRxs9I/AAAAAAAA4sQ/O2xyscr4u_U/s400/tensai_boy.png',
              title='7.數學課本五下8-2節 P106 例題九',
              text='利用平方公里和平方公尺的關係，解決換算和除法應用問題',
              actions=[
                #MessageAction(label='hi', text='hi'),
                URIAction(label='8-2節 P106 例題九',
                          uri='https://www.youtube.com/watch?v=oZMrVNVs7uY')
              ])
          ]))

        #存系統發送的訊息
        stuResp(user_id, time, "影片", "(系統)")
        #print('(系統:', '影片', ')')
        #存系統發送的訊息

      #呼叫OpenAI
      else:
        #增加SYSTEM_MESSAGE
        try:
          #QtoSM=None
          stu_nowq_dic = questions_dic[get_allData(user_id,
                                                   stu_ranQ=1)["stu_ranQ"]]
          QtoSM = '永遠不要直接給出當前題目的答案，當前題目:' + stu_nowq_dic['q']
        except:
          QtoSM = ''
        memory.change_system_message(user_id, QtoSM + SM)
        #增加SYSTEM_MESSAGE

        model = OpenAIModel(api_key=api_key)
        is_successful, _, _ = model.check_token_valid()
        if not is_successful:
          raise ValueError('Invalid API token')
        model_management[user_id] = model
        api_keys[user_id] = api_key
        storage.save(api_keys)
        #msg = TextSendMessage(text='Token 有效，註冊成功')
        #強制註冊

        memory.append(user_id, 'user', text)
        is_successful, response, error_message = model_management[
          user_id].chat_completions(memory.get(user_id),
                                    os.getenv('OPENAI_MODEL_ENGINE'))
        if not is_successful:
          raise Exception(error_message)
        role, response = get_role_and_content(response)
        msg = TextSendMessage(text=response)
        #test
        #print (msg.decode('unicode_escape'))
        #test
        memory.append(user_id, role, response)

        #存GPT-4發送的訊息
        stuResp(user_id, time, response, "(GPT-4)")
        print('(GPT-4:', response, ')')
        #存GPT-4發送的訊息

      #呼叫OpenAI

    #msg訊息格式錯誤回傳
    except ValueError:
      msg = TextSendMessage(text='Token 無效，請重新註冊，格式為 「註冊」 sk-xxxxx')
    except Exception as e:
      memory.remove(user_id)
      if str(e).startswith('Incorrect API key provided'):
        msg = TextSendMessage(text='OpenAI API Token 有誤，請重新註冊。')
      elif str(e).startswith(
          'That model is currently overloaded with other requests.'):
        msg = TextSendMessage(text='已超過負荷，請稍後再試')
      else:
        msg = TextSendMessage(text=str(e))
    #msg訊息格式錯誤回傳

  #print(count)

  #送出給LINE
  line_bot_api.reply_message(event.reply_token, msg)
  #送出給LINE
  print(questions_resp_stast)
  
# 檢查檔案是否存在，如果存在就讀取之前的資料，否則建立一個新的檔案
if os.path.isfile('sturecord.html'):
    print('88888')
    with open('sturecord.html', 'r', encoding='utf-8') as f:
        previous_data = f.readlines()
        print('88887')
        # 只保留前58行的內容
        previous_data = previous_data[:58]
else:
    previous_data = []

# 取得路徑下所有的txt檔案
txt_files = [f for f in os.listdir('sturesp/allresp') if f.endswith('.txt')]

# 創建一個 dictionary 來儲存每個使用者最新的 DataFrame
user_tables = {}
print(user_tables)

# 逐一讀取每個txt檔案，整理成DataFrame，並存儲在 user_tables 中
for txt_file in txt_files:
    user_id = txt_file.split('.')[0]
    with open(f'sturesp/allresp/{txt_file}', 'r') as f:
        data = [eval(line) for line in f]

    # 提取 ID、時間、訊息
    rows = []
    for item in data:
        rows.append({'ID': item['ID'], '時間': item['時間'], '訊息': item['訊息']})

    # 將資料轉換成 DataFrame
    df = pd.DataFrame(rows)

    # 如果使用者已經有表格，則將新的訊息更新至原表格，否則就新增一個新表格
    if user_id in user_tables:
        # 找出更新後的資料
        updated_df = df[df['時間'] > user_tables[user_id]['時間'].max()]
        if not updated_df.empty:
            # 將更新後的表格與原本的表格合併
            user_tables[user_id] = pd.concat([user_tables[user_id], updated_df])
    else:
        user_tables[user_id] = df

# 將每個使用者的 DataFrame 轉換成 HTML 表格，並連接起來
html_tables = []
for user_id, df in user_tables.items():
    html_tables.append(f"<h2>{user_id}</h2>" + df.to_html(index=False))

all_html_tables = '<br>'.join(html_tables)

# 在 sturecord.html 檔案的末尾繼續添加 HTML 表格
with open('sturecord.html', 'w', encoding='utf-8') as f:
    # 將表格包裝在一個<div>元素中，加上padding-left樣式屬性讓表格向右移
  # 將表格包裝在一個<div>元素中，加上padding-left樣式屬性讓表格向右移
  html = f"<div style='text-align:center; padding-left: 50px;'>{all_html_tables}</div>" +  """
    <!-- Option 1: jQuery and Bootstrap Bundle (includes Popper) -->
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-Fy6S3B9q64WdZWQUiU+q4/2Lc9npb8tCaSX9FK7E8HnRr0Jz8D6OP9dO5Vg3Q9ct" crossorigin="anonymous"></script>
</body>
</html>
"""
  f.write(''.join(previous_data) + html)
  print('88876')

#測試新後台

# 檢查檔案是否存在，如果存在就讀取之前的資料，否則建立一個新的檔案
if os.path.isfile('sturecord1.html'):
    with open('sturecord1.html', 'r', encoding='utf-8') as f:
        previous_data1 = f.readlines()
        print('88887')
        # 只保留前65行的內容
        previous_data1 = previous_data1[:65]
else:
    previous_data1 = []

# 取得當天日期，格式為月份和日期，例如 "0509"
today = datetime.today().strftime("%m%d")

# 讀取存有學生資料的資料夾路徑
folder_path = "sturesp/allData/" + today + "/"

# 創建一個空的學生列表
students = []

# 遍歷存有學生資料的資料夾中所有的JSON檔案
for filename in os.listdir(folder_path):
    with open(os.path.join(folder_path, filename), "r") as f:
        # 讀取JSON檔案並解析
        data = json.load(f)

        # 取得學生ID，例如 "Ueff707dbb373a21ccefbf2bbe73f4017"
        student_id = list(data.keys())[0]

        # 取得 "stu_okQnum"、"FQnum_list"、"stu_score" 的數值
        ok_qnums = data[student_id]["stu_okQnum"]
        fq_num_list = data[student_id]["FQnum_list"]
        score = data[student_id]["stu_score"]

        # 將學生資料整理成一個字典，方便之後轉換成DataFrame
        student = {"ID": student_id, "答對題號": ok_qnums, "錯誤清單": fq_num_list, "目前成績": score}

        # 將學生字典加入學生列表中
        students.append(student)

# 將學生列表轉換成DataFrame
df = pd.DataFrame(students)

# 將DataFrame轉換成HTML表格
table_html ='<br>'+ df.to_html(index=False)

#table_html1 = '<br>'.join(table_html)

# 在 sturecord1.html 檔案的末尾繼續添加 HTML 表格
with open('sturecord1.html', 'w', encoding='utf-8') as f:

    # 將表格包裝在一個<div>元素中，加上padding-left樣式屬性讓表格向右移
    html = f"<div style='text-align:center; padding-left: 50px;'>{table_html}</div>" """
        <div style="text-align:center">
            <div style="display:inline-block">

            </div>
        </div>
      <!-- Option 1: jQuery and Bootstrap Bundle (includes Popper) -->
      <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-Fy6S3B9q64WdZWQUiU+q4/2Lc9npb8tCaSX9FK7E8HnRr0Jz8D6OP9dO5Vg3Q9ct" crossorigin="anonymous"></script>
  </body>
  </html>
  """
 
  
  # 將原本的內容和新的表格內容合併
    all_html = previous_data1 + [table_html]

    # 寫入新的內容，從第66行開始
    f.write(''.join(all_html[:65]) + '\n')
    f.write(''.join(all_html[65:]))

#測試新後台

@app.route("/", methods=['GET'])
def index():
  with open(os.path.join('index.html'), 'r', encoding='utf-8') as index:
    html_index = index.read()
  return (html_index)


@app.route("/stuall/", methods=['GET'])
def stuall():
  with open(os.path.join('stuall.html'), 'r', encoding='utf-8') as stuall:
    html_stuall = stuall.read()
  return (html_stuall)


@app.route("/stuone/", methods=['GET'])
def stuone():
  with open(os.path.join('stuone.html'), 'r', encoding='utf-8') as stuone:
    html_stuone = stuone.read()
  return (html_stuone)


@app.route("/contact/", methods=['GET'])
def contact():
  with open(os.path.join('contact.html'), 'r', encoding='utf-8') as contact:
    html_contact = contact.read()
  return (html_contact)


@app.route("/sturecord/", methods=['GET'])
def sturecord():
  with open(os.path.join('sturecord.html'), 'r',
            encoding='utf-8') as sturecord:
    html_sturecord = sturecord.read()
  return (html_sturecord)

@app.route("/sturecord1/", methods=['GET'])
def sturecord1():
  with open(os.path.join('sturecord1.html'), 'r',
            encoding='utf-8') as sturecord1:
    html_sturecord1 = sturecord1.read()
  return (html_sturecord1)

@app.route("/sturecord2/", methods=['GET'])
def sturecord2():
  with open(os.path.join('sturecord2.html'), 'r',
            encoding='utf-8') as sturecord2:
    html_sturecord2 = sturecord2.read()
  return (html_sturecord2)


@app.route("/testall/", methods=['GET'])
def testall():
  with open(os.path.join('testall.html'), 'r',
            encoding='utf-8') as testall:
    html_testall = testall.read()
  return (html_testall)

@app.route("/test0428/", methods=['GET'])
def test0428():
  with open(os.path.join('test0428.html'), 'r',
            encoding='utf-8') as test0428:
    html_test0428 = test0428.read()
  return (html_test0428)

@app.route("/Questions.json/", methods=['GET'])
def QQ():
  with open(os.path.join('Questions.json'), 'r', encoding='utf-8') as QQ:
    html_QQ = QQ.read()
  return (html_QQ)


@app.route("/test.json/", methods=['GET'])
def QqQ():
  with open(os.path.join('test.json'), 'r', encoding='utf-8') as QqQ:
    html_QqQ = QqQ.read()
  return (html_QqQ)

@app.route("/test0508/", methods=['GET'])
def test0508():
  with open(os.path.join('test0508.html'), 'r',
            encoding='utf-8') as test0508:
    html_test0508 = test0508.read()
  return (html_test0508)
  
  # 檢查檔案是否存在，如果存在就讀取之前的資料，否則建立一個新的檔案
  if os.path.isfile('sturecord.html'):
    with open('sturecord.html', 'r', encoding='utf-8') as f:
      previous_data = f.readlines()
      # 只保留前58行的內容
      previous_data = previous_data[:58]
  else:
    previous_data = []

  # 取得路徑下所有的txt檔案
  txt_files = [f for f in os.listdir('sturesp/allresp') if f.endswith('.txt')]

  # 創建一個 dictionary 來儲存每個使用者最新的 DataFrame
  user_tables = {}

  # 逐一讀取每個txt檔案，整理成DataFrame，並存儲在 user_tables 中
  for txt_file in txt_files:
    user_id = txt_file.split('.')[0]
    with open(f'sturesp/allresp/{txt_file}', 'r') as f:
      data = [eval(line) for line in f]

    # 提取 ID、時間、訊息
    rows = []
    for item in data:
      rows.append({'ID': item['ID'], '時間': item['時間'], '訊息': item['訊息']})

    # 將資料轉換成 DataFrame
    df = pd.DataFrame(rows)

    # 如果使用者已經有表格，則將新的訊息更新至原表格，否則就新增一個新表格
    if user_id in user_tables:
      # 找出更新後的資料
      updated_df = df[df['時間'] > user_tables[user_id]['時間'].max()]
      if not updated_df.empty:
        # 將更新後的表格與原本的表格合併
        user_tables[user_id] = pd.concat([user_tables[user_id], updated_df])
    else:
      user_tables[user_id] = df

  # 將每個使用者的 DataFrame 轉換成 HTML 表格，並連接起來
  html_tables = []
  for user_id, df in user_tables.items():
    html_tables.append(f"<h2>{user_id}</h2>" + df.to_html(index=False))

  all_html_tables = '<br>'.join(html_tables)

  # 在 sturecord.html 檔案的末尾繼續添加 HTML 表格
  with open('sturecord.html', 'w', encoding='utf-8') as f:
    # 將表格包裝在一個<div>元素中，加上padding-left樣式屬性讓表格向右移
    htmljump = """<!-- Option 1: jQuery and Bootstrap Bundle (includes Popper) -->
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-Fy6S3B9q64WdZWQUiU+q4/2Lc9npb8tCaSX9FK7E8HnRr0Jz8D6OP9dO5Vg3Q9ct" crossorigin="anonymous"></script>
</body>
</html>"""
    html = f"<div style='text-align:center; padding-left: 50px;'>{all_html_tables}</div>{htmljump}"
    f.write(''.join(previous_data) + html)






if __name__ == "__main__":
  try:
    data = storage.load()
    for user_id in data.keys():
      model_management[user_id] = OpenAIModel(api_key=data[user_id])
  except FileNotFoundError:
    pass
  app.run(host='0.0.0.0', port=8080)





#<body>