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
import utils_balance as ub
from csv import writer

app = Flask(__name__)
app.debug = True

# Recibir los parametros
arg = sys.argv
# Estados del nodo
id_nodo = int(arg[1]) # ID posicion 1
election = False
puerto_nodo = int(arg[2]) # Puerto del contenedor
ip_container = arg[3] # ip del container
puerto_base = int(arg[5]) # puerto base
total_proposer = int(arg[6]) # Total de proposer

# Datos del coordinador
puerto_cor = 0
id_cor = 0
without_coordina = False
puertos_kill = []
verificar = False

# Verifica si es el coordinador
if (arg[4] == '1'):
    coordina = True
    id_cor = id_nodo
else:
    coordina = False

pet =0

# Info of aceptors
ip_acep = arg[7] # Ip base of aceptors
puerto_acep = int(arg[8]) # Puerto base de aceptors
num_acep = int(arg[9]) # Cantidad de aceptors
aceptors_kill = list()
class NodeBully:
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
node_local = NodeBully(ide=id_nodo,
                       ip_nodo=ip_container,
                       puerto=puerto_nodo)

proposer_lider = NodeBully(ide=0,
                       ip_nodo='0',
                       puerto=0)

nodos_proposer = list()

# ------------------------------------------ BULLY  ------------------------------------
# Inicializa otros nodos proposer para conocerlos
def init_nodos(m):
    global puerto_base
    global total_proposer
    global node_local
    nodos = list()
    for x in range(total_proposer):
        if (node_local.puerto != (puerto_base+x)):
            aux = NodeBully(ide=x+1,
                            ip_nodo=node_local.ip_nodo,
                            puerto=puerto_base+x)
            nodos.append(aux)
    return nodos
        
# Recibe los datos del nuevo coordinador
@app.route('/COORDINATOR', methods = ['POST'])
def fun_coordinator():
    global pet
    global election
    global proposer_lider
    # recibimos json
    message = request.get_json()
    # Actualizamos el proposer lider
    proposer_lider.set_ide(message['id'])
    proposer_lider.set_ip_nodo(message['ip'])
    proposer_lider.set_puerto(message['puerto'])
    # Coordinador llegó
    app.logger.info('------ COORDINATOR '+str(proposer_lider.ide)+' ------')
    election = False
    without_coordina = False
    pet =0
    # Comienza el proceso de verificacion
    monitor = threading.Thread(target=fun_verificar)
    monitor.start()
        
    return jsonify({'response':'RECIBIDO'})

# Hace el proceso de election
@app.route('/ELECTION',methods = ['POST'])
def fun_election():
    global election
    global node_local
    if (election==True):
        # Recibi el post
        message = request.get_json()
        # Id y puerto del nodo que hace peticion de election
        id_vecino = message['id']
        # app.logger.info('------ ELECTION CON EL NODO '+str(id_vecino) + ' ------')
        # Si el nodo actual es mayor
        if (node_local.ide>id_vecino):
            # app.logger.info('------ SOY MAYOR ------')
            return jsonify({'response':'OK'})    
        # Si el vecino es mayor
    else:
            # app.logger.info('------ SOY MENOR ------')
        return jsonify({'response':'NO'})

# Funcion de verificacion del coordinator
def fun_verificar():
    global pet
    global election
    global without_coordina
    global proposer_lider
    global node_local
    
    while True:
        try:
            if (election == False):
                # Verificamos si no somos el mismo
                if (proposer_lider.puerto == node_local.puerto):
                    break
                time.sleep(5+(id_nodo))
                url = proposer_lider.ip_nodo+':'+str(proposer_lider.puerto)+'/PRUEBA'
                headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
                req = requests.post('http://'+url, headers=headers)
                # app.logger.info('------ SOY EL NODO No.'+str(id_nodo)+' - '+str(puerto_nodo)+'------')
                pet += 1
                app.logger.info('------('+str(pet)+') ACTIVO LIDER ='+str(proposer_lider.ide)+' - ('+str(node_local.puerto)+')------')
        except requests.exceptions.ConnectionError:
            # Proceso de election
            puertos_kill.append(proposer_lider.puerto)
            # Notifica a todos de election
            time.sleep(10)
            if(election == False and without_coordina == False):
                for proposer in nodos_proposer:
                    if (proposer.puerto not in puertos_kill): 
                        # requests
                        # app.logger.info('------ ME DI CUENTA ------')
                        app.logger.info('------ ME DI CUENTA ('+str(node_local.ide)+') ------')
                        url = proposer.ip_nodo+':'+str(proposer.puerto)+'/PRE'
                        # url = '148.247.201.221:'+puerto+'/PRE'
                        # Enviar petricion de eleccion
                        headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
                        req = requests.post('http://'+url, headers=headers)
                        response_json = req.json()
                        app.logger.info('------ '+response_json['response']+' ('+str(proposer.ide)+') ------')
                # Inicio proceo de election
                app.logger.info('------ PROCESO ------')
                election = True
                init()
            break
    
# Verificacion de actividad
@app.route('/PRE',methods = ['POST'])
def pre():
    global election
    election = True
    without_coordina = True
    app.logger.info('------ ELECTION ------')
    return jsonify({'response':'ELECTION'})

# Verificacion de actividad
@app.route('/INICIO_ELECTION',methods = ['POST'])
def inicio_election():
    global election    
    # time.sleep(10)
    init()
    return jsonify({'response':'OK'})

# Verificacion de actividad
@app.route('/PRUEBA',methods = ['POST'])
def prueba():
    global proposer_lider
    app.logger.info('------ Verificacion '+str(proposer_lider.ide)+' ------')
    return jsonify({'response':'SI'})

def init():
    global coordina
    global proposer_lider
    global node_local
    # Inicia la election
    cont=0
    for proposer in nodos_proposer:
        if (node_local.puerto < proposer.puerto):
            if (proposer.puerto not in puertos_kill):
                # requests
                url = proposer.ip_nodo+':'+str(proposer.puerto)+'/ELECTION'
                # url = '148.247.201.221:'+puerto+'/ELECTION'
                datas = {
                    'id':node_local.ide,
                    'ip':node_local.ip_nodo,
                    'puerto':node_local.puerto
                }
                try:
                    headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
                    req_i = requests.post('http://'+url, data=json.dumps(datas), headers=headers)
                    # Recibir
                    responde_json_ = req_i.json()
                    # Existe uno mayor
                    if (responde_json_['response'] == 'OK'):
                        app.logger.info('------ ('+str(proposer.puerto)+') OK ------')
                        # Se manda notifiacion al primer mayor
                        if(cont==0):
                            mayor_puerto = proposer.puerto
                            mayor_ip = proposer.ip_nodo
                            cont = 1
                except requests.exceptions.ConnectionError:
                    print('')
    # Envia la notificion al siguiente puerto mayor a que haga la election
    if (cont == 1):
        url = mayor_ip+':'+str(mayor_puerto)+'/INICIO_ELECTION'
        # url = '148.247.201.221:'+mayor_puerto+'/INICIO_ELECTION'
        try:
            headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
            req = requests.post('http://'+url, data=json.dumps(datas), headers=headers)
            # Recibir
            responde_json = req.json()
            # Existe uno mayor
            if (responde_json['response'] == 'OK'):
                app.logger.info('------ NODO NUEVO PARA ELECTION '+str(mayor_puerto)+' ------')
                # # Se manda notifiacion al primer mayor
                # if(cont==0):
                #     mayor_puerto = puerto
                #     cont = 1
        except requests.exceptions.ConnectionError:
            print('')   
    else:
        # Soy el nuevo coordinador
        proposer_lider = node_local
        coordina = True
        app.logger.info('------ SOY EL NUEVO COORDINATOR No.'+str(node_local.ide)+'------')
        for proposer in nodos_proposer:
            if (proposer.puerto not in puertos_kill):
        # for puerto in puertos:
            # if (puerto not in puertos_kill):
                # requests
                url = proposer.ip_nodo+':'+str(proposer.puerto)+'/COORDINATOR'
                # url = '148.247.201.221:'+puerto+'/COORDINATOR'
                datas = {
                    'id':node_local.ide,
                    'ip':node_local.ip_nodo,
                    'puerto':node_local.puerto
                }
                headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
                req = requests.post('http://'+url, data=json.dumps(datas), headers=headers)
                # Recibir
                responde_json = req.json()
                app.logger.info('------ SE NOTIFICO AL NODO '+str(proposer.puerto) + ' - ' + responde_json['response']+' ------')

# ------------------------------------------ PAXOS PROPOSER ------------------------------------
def envio_request_witout_return(url,comand,datas):
    headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
    req = requests.post(url+comand, data=json.dumps(datas), headers=headers)
    return 1

# Inicializamos todos los aceptors
def init_aceptors(num_acep,puerto_acep,ip_acep):
    global node_local
    nodos = list()
    for x in range(num_acep):
        aux = NodeBully(ide=x+1,
                        ip_nodo=ip_acep,
                        puerto=puerto_acep+x)
        nodos.append(aux)
    return nodos

aceptors_nodos = init_aceptors(num_acep,puerto_acep,ip_acep)

# Prepare peticions for aceptors
@app.route('/PREPARE',methods =['POST'])
def prepare():
    global aceptors_nodos
    global aceptors_kill
    # recibe los parametros para hacer el balanceo
    message = request.get_json()
    # Recibe los datos    
    N = message['N']
    k_ = message['K']
    data_balance = message['data_balance']
    type_balance = message['type_balance']
    type_cluster = message['type_cluster']
    name = message['name']
    # Numero de trabajadores son los dispobibles en paxos
    # Inicia el PREPARE
    inicio_paxos = time.time()
    workers = 0
    workers_available = list()
    for aceptor in aceptors_nodos:
        
        try:
            if (aceptor.ide not in aceptors_kill):
                url = aceptor.ip_nodo+':'+str(aceptor.puerto)+'/PROMISE'
                datas = {
                    'N':N
                }
                # Hace la peticion
                headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
                req = requests.post('http://'+url, data=json.dumps(datas), headers=headers)
                responde_json = req.json()
                app.logger.info('------ ACEPTOR '+str(aceptor.ide) + ' - ' + responde_json['response']+' ------')
                if(responde_json['response']=='PROMISE'):
                    workers = workers + 1
                    workers_available.append(aceptor)
        # en caso de que uno falle
        except requests.exceptions.ConnectionError:
            aceptors_kill.append(aceptor.ide)
            
        
    
    # Se envia mensaje de confirmacio
    # ACCEPT
    app.logger.info('------ '+ str(N)+' - SE ENCUENTRAN DISPONIBLES ' + str(workers) + ' ------')
    if (workers>0):
        workers_no=0
        workers_aux = workers_available
        workers_kill = list()
        for work in workers_aux:
            try:
                url = work.ip_nodo+':'+str(work.puerto)+'/ACCEPT'
                datas = {
                    'N':N
                }
                # Hace la peticion
                headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
                req = requests.post('http://'+url, data=json.dumps(datas), headers=headers)
                responde_json = req.json()
                app.logger.info('------ ACCEPTOR '+str(work.ide) + ' - ' + responde_json['response']+' ------')
                # En caso de que no la llegue a prometer
                if(responde_json['response']!='ACEPTO'):
                        workers = workers - 1
                        workers_no = workers_no + 1
                        workers_kill.append(work.ide)
            except requests.exceptions.ConnectionError:
                # En caso de que no se encuentre o falle a la hora de la confirmación
                workers = workers - 1
                workers_no = workers_no + 1
                workers_kill.append(work)
        fin_paxos = time.time()
        append_list_as_row('./data/tiempos_consenso.csv', [workers,(fin_paxos-inicio_paxos)])
        # --------------------------- Termina paxos ya se cuentos workers tengo ----------------------------------
    # Inicio el balanceo
    if (workers>0):
        init_data = ub.init_workres_array(workers)
        data_clus = ub.read_CSV(message['name']) # DataPreprocess
        
        # numero AÑOS DIAS O MESES
        type_balance_str = ub.type_blane_cond(data_balance)
        list_balance = data_clus[type_balance_str].unique()
        
        if (type_balance=='RR'): # Balanceador Round Robin
            init_data = ub.RaoundRobin(init_data,list_balance,workers)
        elif (type_balance=='PS'):# Balanceador PseudoRandom
            init_data = ub.PseudoRandom(init_data,list_balance,workers)
        elif (type_balance=='TC'):# Balanceador TwoChoices
            init_data = ub.TwoChoices(init_data,list_balance,workers)
        else:# Balanceador Round Robin
            init_data = ub.RaoundRobin(init_data,list_balance,workers)
        
    # app.logger.error(puertos_online)
    # peticiones = []
    # inicio=time.time()
    
    # with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    # Enviar a todos los learners
    
    
        for x in range(workers):
            if (workers_available[x].ide not in workers_kill):
                if (len(init_data[x])>0):
                    concac=[]
                    for val in init_data[x]:
                        # app.logger.info(val)
                        concac.append(data_clus[data_clus[type_balance_str]==val])
                    data_fin = pd.concat(concac)
                    name = "ID_"+str(workers_available[x].ide)+"_Port_"+str(workers_available[x].puerto)+"_LD="+type_balance+"_DLB="+data_balance
                    data_fin.to_csv("./data/"+name+".csv")
                    data_clus_n = {
                        "K": k_,
                        "name": name,
                        "type_cluster":type_cluster,
                        "need":workers
                        }
                        
                    url = "http://"+workers_available[x].ip_nodo+":"+str(workers_available[x].puerto)
                    # req = envio_request_witout_return(url,"/LEARNER",data_clus_n)
                        
        workers_available = list()
        return jsonify({'response':'------ Termino -------'})
    else:
        app.logger.info('------ No hay trabajadores disponibles ------')
        return jsonify({'response':'------ No hay trabajadores disponibles ------'})
        
    
        
# ------------------------------------------ START CONTAINER -----------------------------------
# Iniciañizar todos los proposer
nodos_proposer = init_nodos(m=total_proposer)

def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='\n') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)  
        # Add contents of list as last row
        csv_writer.writerow(list_of_elem)
        
# Coordinador
if (coordina==True):
    # global node_local
    # global nodos_proposer
    proposer_lider = node_local
    # Notifico que es el coordinador
    app.logger.info('------ SOY EL COORDINADOR - No.'+str(node_local.ide) + ' ------')
    time.sleep(10)
    app.logger.info(str(len(nodos_proposer))+' lista ------- ')
    for proposer in nodos_proposer:
        if (proposer.puerto not in puertos_kill):            
            # requests
            # node_local.ip_nodo
            url = proposer.ip_nodo+':'+str(proposer.puerto)+'/COORDINATOR'
            app.logger.error(url)
            # url = '148.247.201.221:'+puerto+'/COORDINATOR'
            datas = {
                'id':node_local.ide,
                'ip':node_local.ip_nodo,
                'puerto':node_local.puerto
            }
            headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
            req = requests.post('http://'+url, data=json.dumps(datas), headers=headers)
            # Recibir
            responde_json = req.json()
            app.logger.info('------ SE NOTIFICO AL NODO '+str(proposer.ide) + ' - ' + responde_json['response']+' ------')
        
if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)
