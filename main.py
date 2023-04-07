
from base64 import encode
from codecs import escape_decode
from crypt import methods
from http import HTTPStatus
from http.client import HTTPResponse
from operator import indexOf
from optparse import Option
from re import search
from tkinter.tix import Tree
from typing import List, Optional, Set, Literal, Union
from typing_extensions import Self
from urllib import response
from pydantic import BaseModel, HttpUrl, Json
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from redis_om import get_redis_connection, HashModel, JsonModel, Field, Migrator, EmbeddedJsonModel
import json, sys
import redis
import time
import datetime
from time import strftime
import requests

from redis.commands.search.query import Query


app = FastAPI()

origins = ['http://localhost',
           'http://localhost:3000',
           'http://localhost.tiangolo.com',
            'https://localhost.tiangolo.com',
            'http://172.30.1.11:3000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],

)



reDB = redis = get_redis_connection(
    host = "localhost",
    port = 6379,
    db = 0,
    decode_responses=True,
    charset="utf-8"
)


class Marketform(BaseModel):
    market: str = Field(index=True)
    goodsname: str = Field(index=True)
    price: int
    deliver: int
    totalprice: int
    img: HttpUrl
    href: HttpUrl
    
    
    
    


class Form(JsonModel):
    path: str = Field(index=True)
    keyword: str = Field(index=True)
    refreshtime: str = time.strftime('%H:%M:%S',time.localtime(time.time()))
    crawlstate: bool
    
    local: Union[list[Marketform], None] = None
    overseas: Union[list[Marketform], None] = None
    
    
    

    
    class Meta:
        database = redis
        

class Autokwd(JsonModel):
    path: str = Field(index=True)
    autokwd: str = Field(index=True)
    
    class Meta:
        database = redis
        
        
def filterKeyword(data):
    data = data.replace('-', '\\-').replace(' ', '\\ ').replace(',', '\\,').replace('.','\\.')
    return data
        

@app.post('/goods') #상품등록
def gamePost(form: Form):
    
    form.refreshtime = time.strftime('%H:%M:%S',time.localtime(time.time()))
    
    json_form = jsonable_encoder(form)
    reDB.execute_command('JSON.SET', 'item:'+form.keyword, '.', json.dumps(json_form))
    
    return '업로드 성공'

@app.post('/autokwd')
def autoKwd(kwd: Autokwd):
    json_form = jsonable_encoder(kwd)
    reDB.execute_command('JSON.SET', 'kwd:'+kwd.autokwd, '.', json.dumps(json_form))
    
    



   
@app.get('/{path}') #경로 검색
def get_path_all(path:str):
    pathAll = []
    
    
    totalNum = reDB.ft('pathIdx').search(path).total
    
    
    
    for i in range(0, totalNum):
        pathAll.append(json.loads(reDB.ft('pathIdx').search(path).docs[i].json))
    
    
    
    
    return pathAll



@app.get('/autokwd/{autokwd}')
def get_autokwd(autokwd:str):
    textList = []
    
    totalNum = reDB.ft('keywordIdx').search(autokwd).total
    
    for i in range(0, totalNum):
        textList.append(json.loads(reDB.ft('keywordIdx').search(Query(autokwd).paging(0, 1000)).docs[i].json))
        
    if len(textList) == 0:
        textList.append('')
    
    return textList

    
@app.get('/goods/{keyword}') #굿즈 이름 검색
def get_goods_path(keyword:str):
    gameList = []
    
    
    
    totalNum = reDB.ft('searchMatchIdx').search("@keyword:{"+filterKeyword(keyword)+"}").total
    
    for i in range(0,totalNum):
        
        gameList.append(json.loads(reDB.ft('searchMatchIdx').search("@keyword:{"+filterKeyword(keyword)+"}").docs[i].json))
        
    
    if len(gameList) == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    
    return gameList
    

    


@app.patch('/goods/{keyword}')
def crawlState_True(keyword:str, state:str):
    
    
    reDB.execute_command('JSON.SET', 'item:'+keyword, '$.crawlstate', state)
    raise HTTPException(status_code=200, detail='CrawlState: '+state)



@app.delete('/goods/{keyword}') #게임이름으로 게임 삭제
def delete(keyword:str):
    
    reDB.execute_command("FT.DEL", "keywordIdx", "item:"+keyword)
    return '삭제 성공'




