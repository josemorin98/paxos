import hashlib
import numpy as np
import requests
import json
import time
import sys
from csv import writer
from threading import Thread


arg = sys.argv

def envio_request(url,comand):
    headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
    req = requests.post(url+comand, headers=headers)
    return req.json() 


url = 'http://148.247.201.222:1501/PREPARE'

for z in range(1,501):
    print(z)
    datas = {
            'N':z,
            'K':[3],
            'data_balance':'D',
            'type_balance':'RR',
            'name':'DataPreproces',
            'type_cluster':'Kmeans',
        }
    headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
    req = requests.post(url,data=json.dumps(datas), headers=headers)
    json_req = req.json()
    print(json_req['response'])
    time.sleep(5)
    
