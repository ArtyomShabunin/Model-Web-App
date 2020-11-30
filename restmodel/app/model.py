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
        self.cursor.execute("""SELECT filename FROM Modelselection WHERE Name='{}'""".format(name))
        file_name = self.cursor.fetchone()[0]
        os.system(r'c:\SimInTech64\bin\mmain.exe  "..\..\model-web-app\restmodel\simintech\modbus_control\modbus_control.prt" /setparameter COMMAND_file_name {} /nomainform /hide /run'.format(file_name))
    #Запись в базу, как отдельный процесс
        p_1 = Process(target=self.write_to_db())
        p_1.start()
        
		
		
    def write_to_db(self):
	#Считывание данных по модбас
        
        self.master_signal = modbus_tcp.TcpMaster(host='localhost',port=1503)
        time.sleep(10)
        self.cursor.execute(""" SELECT regs FROM Variable ORDER BY id DESC LIMIT 1""")
        size_bits = self.cursor.fetchone()[0]
        self.cursor.execute(""" SELECT id FROM Variable ORDER BY id DESC LIMIT 1""")
        id_next = self.cursor.fetchone()[0]
        id_vals=id_next-size_bits
        self.cursor.execute(""" SELECT regs FROM Variable WHERE id = {}""".format(id_vals-1))
        size_vals = int((self.cursor.fetchone()[0]+2)/2)
		
        start_vals=np.zeros(int(size_vals*2/110)+2)
        count_vals=np.zeros(int(size_vals*2/110)+2)
        start_bit = np.zeros(int(size_bits/2000)+2)
        count_bit = np.zeros(int(size_bits/2000)+2)
        start_bit[0] = 0
        count_bit[0] = 2000
        start_vals[0]=0
        count_vals[0]=110
        data = []
        for m in range(1,int(size_vals*2/110)+2):
            start_vals[m] = start_vals[m-1]+ 110
            count_vals[m] = 110
            if m == int(size_vals*2/110):
                count_vals[m] = size_vals*2 - start_vals[m]
            data += self.master_signal.execute(1,cst.READ_HOLDING_REGISTERS, int(start_vals[m-1]),int(count_vals[m-1]))
        for m in range(1,int(size_bits/2000)+2):
            start_bit[m] = start_bit[m-1] + 2000
            count_bit[m] = 2000
            if m == int(size_bits/2000):
                count_bit[m] = size_bits - start_bit[m]
            data += self.master_signal.execute(1,cst.READ_COILS, int(start_bit[m-1]),int(count_bit[m-1]))
        n=np.zeros(int(len(data)-size_vals))
        for i in range(size_vals):
            value = struct.unpack('>f', struct.pack('>H', data[1]) + struct.pack('>H', data[0]))[0]
            n[i]=float('{:.3f}'.format(value))
            data = data[2:]
        for i in range(len(data)):  
            n[i+size_vals]=data[i]	
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
                            querry = querry + '({},{},{},{}),'.format("'{}'",j,achive_id,int(id_next-size_vals-size_bits) + i)
                        if i == len(data)-1:    
                            querry = querry + '({},{},{},{})'.format("'{}'",j,achive_id,int(id_next-size_vals-size_bits) + i)
                        current_time = datetime.datetime.now()
                        querry = querry.format(current_time)
                    self.cursor.execute('{}'.format(querry))
                    self.conn.commit()
                data1 = data
                time.sleep(1)
                data = []
                for m in range(1,int(size_vals*2/110)+2):
                    data += self.master_signal.execute(1,cst.READ_HOLDING_REGISTERS, int(start_vals[m-1]),int(count_vals[m-1]))
                for m in range(1,int(size_bits/2000)+2):
                    data += self.master_signal.execute(1,cst.READ_COILS, int(start_bit[m-1]),int(count_bit[m-1]))
                    

                n1=np.zeros(int(len(data)-size_vals))
                for i in range(size_vals):
                    value = struct.unpack('>f', struct.pack('>H', data[1]) + struct.pack('>H', data[0]))[0]
                    n1[i]=float('{:.3f}'.format(value))
                    data = data[2:]
                for i in range(len(data)):  
                    n1[i+size_vals]=data[i]	
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
            g = open('simintech/test_model/modbus_signal/txt/bits.txt')
        if model_id == 2:
            f = open('simintech/model/modbus_signal/txt/vals.txt')
            g = open('simintech/model/modbus_signal/txt/bits.txt')
	#Запись имен в базу данных
        fd = f.readlines()
        for i in range(0,len(fd)):
            fd[i]=list(fd[i])
            for j in range(0,len(fd[i])):
                if fd[i][j] == '\n':
                    fd[i][j] = '' 
            fd[i] = "".join(fd[i])
        for i in range(0,len(fd)):
            self.cursor.execute("""INSERT INTO Variable (name,type,regs,max_value,min_value,model_id) VALUES ('{}','integer','{}','10000','0','{}')""".format(fd[i],i*2,model_id))
            self.conn.commit()
        gd = g.readlines()
        for i in range(0,len(gd)):
            gd[i]=list(gd[i])
            for j in range(0,len(gd[i])):
                if gd[i][j] == '\n':
                    gd[i][j] = '' 
            gd[i] = "".join(gd[i])
        self.cursor.execute(""" SELECT id FROM Variable ORDER BY id DESC LIMIT 1""")
        id = self.cursor.fetchone()[0]
        for i in range(0,len(gd)):
            self.cursor.execute("""INSERT INTO Variable (id,name,type,regs,max_value,min_value,model_id) VALUES ('{}','{}','boolean','{}','1','0','{}')""".format(id+i+1,gd[i],i,model_id))
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