from app import app
import os
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
from threading import Thread
import time
import struct
import pandas as pd
from multiprocessing import Process
import numpy as np
import subprocess  
import psycopg2
import datetime

class Model(object):
   
	
    def __init__(self):
        #Подключение к Modbus
        self.master_control = modbus_tcp.TcpMaster(host='localhost',port=1502)
        #self.master_signal = modbus_tcp.TcpMaster(host='localhost',port=1503)
		#Подключение к базе данных
        self.conn = psycopg2.connect(database="variable", user="postgres", password="postgres", host="10.202.242.95", port="6543")
        self.cursor = self.conn.cursor()
        self.cursor.execute("ROLLBACK")
		#Начальное состояние кооманд
        self.cursor.execute("UPDATE State SET value = {} WHERE name = 'start_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name = 'pause_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name = 'stop_model'".format(0))

        
        
    def init(self,name):
	#Открытие модели по имени
        self.cursor.execute("""SELECT id FROM Modelselection WHERE Name='{}'""".format(name))
        model_id= self.cursor.fetchone()[0]
        os.system(r'c:\SimInTech64\bin\mmain.exe /hide "..\..\..\..\tpp-simulator\SH\Control\restmodel\simintech\modbus_control\modbus_control.prt" /nomenu /hidemenus /noborder /setparameter COMMAND_ID {} /run'.format(model_id))
    #Запись в базу, как отдельный процесс
        p_1 = Process(target=self.write_to_db())
        p_1.start()
        
		
		
    def write_to_db(self):
	#Считывание данных по модбас
        
        self.master_signal = modbus_tcp.TcpMaster(host='localhost',port=1503)
        self.cursor.execute(""" SELECT id FROM Variable ORDER BY id DESC LIMIT 1""")
        size = self.cursor.fetchone()[0]
        k=np.zeros(int(size*2/110)+2)
        a=np.zeros(int(size*2/110)+2)
        k[0]=0
        a[0]=110
        data = []
        for m in range(1,int(size*2/110)+2):
            k[m] = k[m-1]+ 110
            a[m] = 110
            if m == int(size*2/110):
               a[m] = size*2 - k[m]
            data += self.master_signal.execute(1,cst.READ_HOLDING_REGISTERS, int(k[m-1]),int(a[m-1]))
        n=np.zeros(int(len(data)/2))
        for i in range(int(len(data)/2)):
            value = struct.unpack('>f', struct.pack('>H', data[1]) + struct.pack('>H', data[0]))[0]
            n[i]=float('{:.3f}'.format(value))
            data = data[2:]	
        data=pd.Series(n)
        while True:
	    #Опрос базы данных на значение работы проекта
            self.cursor.execute(""" SELECT id FROM Achive ORDER BY id DESC LIMIT 1""")
            achive_id = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT * FROM State WHERE id = 1")
            for row in self.cursor.fetchall():
                run=row[2]
            if run != True:
                break
            else: 	
                if len(data)>0:			
                    for i,j in enumerate(data):
                        if i == 0:
                            querry = """INSERT INTO Measurement (time,value,achive_id,variable_id) VALUES"""
                        if (i < len(data)-1) :
                            querry = querry + '({},{},{},{}),'.format("'{}'",j,achive_id,data.index[i]+1)
                        if i == len(data)-1:    
                            querry = querry + '({},{},{},{})'.format("'{}'",j,achive_id,data.index[i]+1)
                        current_time = datetime.datetime.now()
                        querry = querry.format(current_time)
                    self.cursor.execute('{}'.format(querry))
                    self.conn.commit()
                data1 = data
                time.sleep(1)
                data = []
                for m in range(1,int(size*2/110)+2):
                    data += self.master_signal.execute(1,cst.READ_HOLDING_REGISTERS, int(k[m-1]),int(a[m-1]))
                    

                n1 = np.zeros(int(len(data)/2))
                for i in range(int(len(data)/2)):
                    value = struct.unpack('>f', struct.pack('>H', data[1]) + struct.pack('>H', data[0]))[0]
                    n1[i]=float('{:.3f}'.format(value))
                    data = data[2:]
                data=pd.Series(n1)
                data = data[abs(data1 - data) > 1e-5]  
                #if len(data)>0:				
                 #   self.cursor.execute('{}'.format(querry))
                  #  self.conn.commit()
                time.sleep(1)
				
    def create_model(self,name):
        self.cursor.execute("""SELECT id FROM Modelselection WHERE Name='{}'""".format(name))
        model_id= self.cursor.fetchone()[0]
        if model_id == 1:
            f = open('simintech/test_model/modbus_signal/txt/vals.txt')
        if model_id == 2:
            f = open('simintech/model/modbus_signal/txt/vals.txt')
	#Запись имен в базу данных
        fd = f.readlines()
        for i in range(0,len(fd)):
            fd[i]=list(fd[i])
            for j in range(0,len(fd[i])):
                if fd[i][j] == '\n':
                    fd[i][j] = '' 
            fd[i] = "".join(fd[i])	
        for i in range(0,len(fd)):
            self.cursor.execute("""INSERT INTO Variable (id,name,regs,max_value,min_value,model_id) VALUES ('{}','{}','{}','10000','0','{}')""".format(i+1,fd[i],i*2,model_id))
            self.conn.commit()
		
		
	
		
        
		
		
		
    
    def start(self):
	#Передача по ТСР команды старт
        self.master_control.execute(1, cst.WRITE_MULTIPLE_REGISTERS,6,output_value=[0,16256])
	#Передача в базу данных значений состояния проекта
        self.cursor.execute("UPDATE State SET value = {} WHERE name='start_model'".format(1))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='pause_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='stop_model'".format(0))
        self.conn.commit()
	#Создание архива
        if self.pause != True:
            self.cursor.execute("""INSERT INTO Achive (datetime) VALUES ('{}')""".format(datetime.datetime.now()))
        
        self.write_to_db()
	
    def pause(self):
	#Передача по ТСР команды пауза
        self.pause = True
        self.master_control.execute(1,cst.WRITE_MULTIPLE_REGISTERS,0,output_value=[0,16256])
	#Передача в базу данных значений состояния проекта
        self.cursor.execute("UPDATE State SET value = {} WHERE name='start_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='pause_model'".format(1))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='stop_model'".format(0))
        self.conn.commit()
	
    def stop(self):
	#Передача по ТСР команды стоп
        self.pause = False
	#Передача в SimInTech по модбас команды стоп
        self.cursor.execute("UPDATE State SET value = {} WHERE name='start_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='pause_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='stop_model'".format(1))
        self.conn.commit()
        self.master_control.execute(1,cst.WRITE_MULTIPLE_REGISTERS,4,output_value=[0,16256])

		
    def save_restart(self):
	#Передача по ТСР команды сохранить рестар
        self.master_control.execute(1,cst.WRITE_MULTIPLE_REGISTERS,8,output_value=[0,16256])
		
    def read_restart(self):
	#Передача по ТСР команды открыть рестарт
        self.master_control.execute(1,cst.WRITE_MULTIPLE_REGISTERS,10,output_value=[0,16256])
	#Передача в базу данных значений состояния проекта
        self.cursor.execute("UPDATE State SET value = {} WHERE name='start_model'".format(1))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='pause_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='stop_model'".format(0))
        self.conn.commit()
		

	
	
		

if __name__ == '__main__':
    app.run(debug=True)