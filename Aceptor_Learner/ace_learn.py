from flask import Flask, request
from flask import Response
from flask import jsonify
import json
import threading
import requests
import sys
import queue
import time
import pandas as pd
import utils_cluster as uc
from concurrent.futures import ThreadPoolExecutor
import os

app = Flask(__name__)
app.debug = True

# Recibir los parametros
arg = sys.argv
# Estados del nodo
ip_container = arg[1] # ip del container
puerto_nodo = int(arg[2]) # Puerto del contenedor
puerto_base = int(arg[3]) # puerto base
total_aceptor = int(arg[4]) # Total de proposer
id_nodo = int(arg[5]) # ID

class NodeAceptor:
    def __init__(self,ide,ip_nodo,puerto):
        self.ide = ide
        self.ip_nodo = ip_nodo
        self.puerto = puerto
        
    def set_ide(self,ide):
        self.ide = ide
    
    def set_ip_nodo(self,ip):
        self.ip_nodo = ip
        
    def set_puerto(self,puerto):
        self.puerto = puerto
    

# Creamos nodo local
aceptor_local = NodeAceptor(ide=id_nodo,
                       ip_nodo=ip_container,
                       puerto=puerto_nodo)


# Inicializamos todos los aceptors
def init_aceptors(num_acep,puerto_acep,ip_acep):
    global aceptor_local
    nodos = list()
    for x in range(num_acep):
        aux = NodeAceptor(ide=x+1,
                        ip_nodo=ip_acep,
                        puerto=puerto_acep+x)
        nodos.append(aux)
    return nodos


# Inicializaos loa aceptadores
aceptors_nodos = list()
aceptors_nodos = init_aceptors(num_acep=total_aceptor,puerto_acep=puerto_base,ip_acep=ip_container)
# registro de peticiones
# Debe ser secuencial el numero de k
peticiones_N = 0

# ------------------------------------------ PAXOS PROMISE ------------------------------------
# Prepare peticions for aceptors
@app.route('/PROMISE',methods =['POST'])
def prepare():
    global aceptors_nodos
    global peticiones_N
    # recibe los parametros para devolver la promesa
    message = request.get_json()
    # Recibe los datos    
    id_pet = message['N']
    # Esta k en el registro
    if (id_pet <= peticiones_N):
        app.logger.info(' - NO PROMISE -')
        return jsonify({'response':'IGUAL o MENOR',
                        'N':id_pet})
    else:
        peticiones_N = id_pet
        app.logger.info('PROMISE')
        return jsonify({'response':'PROMISE',
                        'N':id_pet})

# ------------------------------------------ PAXOS ACCEPTED -----------------------------------
# Aceptar propuesta
@app.route('/ACCEPT', methods=['POST'])
def accepted():
    global aceptors_nodos
    global peticiones_N
    # recibe los parametros para devolver la promesa
    message = request.get_json()
    # Valore de peticion
    id_pet_ = message['N']
    # Verificar si la acepto
    if (id_pet_ == peticiones_N):
        # app.logger.info('IGUAL')
        app.logger.info('ACEPTO')
        return jsonify({'response':'ACEPTO',
                        'N':peticiones_N})
    else:
        return jsonify({'response':'RECHAZO',
                        'N':peticiones_N})
    
# ------------------------------------------ PAXOS LEARNER -----------------------------------
def prueba_clus(k_,type_cluster,data_clima,name,wor):
    # app.logger.error(k_)
    data_p =data_clima.iloc[:,[7,8,9,10]]
    for k in k_:
        # KMEANS
        if (type_cluster=="Kmeans"):
            # llamado del clustering
            inicio = time.time()
            k_labels,it = uc.K_means(k,data_p)
            cluster="Kmeans"
            fin = time.time()
            app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' ------')
        elif (type_cluster=="GM"):
            inicio = time.time()
            k_labels = uc.MixtureModel(k,data_p)
            cluster="GaussianMixture"
            fin = time.time()
            app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' ------')
        else:
            inicio = time.time()
            k_labels,it = uc.K_means(k,data_p)
            cluster="Kmeans"
            fin = time.time()
            app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' ------')
        # data send
        # append_list_as_row('./data/tiempos_carga.csv', [wor,cluster,(fin-inicio)])
        data_clima['clase']=k_labels
        data_clima.to_csv("./data/results/Clus_"+name+"_DataClust_K="+str(k)+"_"+str(cluster)+".csv")
        return 1
 
 
@app.route('/LEARNER', methods=['POST'])
def learner():
    message = request.get_json()
    # recibir K
    k_ = message['K']
    name = message['name']
    type_cluster = message['type_cluster']
    wor = message['need']
    
    data_clima = uc.read_CSV(name)
    # data_p =data_clima.iloc[:,[7,8,9,10]]
    # prueba_clus(k_,type_cluster,data_p,name,wor)
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # app.logger.info('executoooooor')
        executor.submit(prueba_clus,k_,type_cluster,data_clima,name,wor)
    return jsonify({'response':'Hare tu trabajo'})
if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)
