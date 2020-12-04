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
import datetime
from sqlalchemy import create_engine
from pymodbus.client.sync import ModbusTcpClient

import subprocess
from datetime import timedelta

class Model(object):
   
	
    def __init__(self):
        #Подключение к Modbus
        self.master_control = modbus_tcp.TcpMaster(host='localhost',port=1502)
		#Подключение к базе данных
        self.conn = create_engine('postgresql://postgres:postgres@10.202.242.95:6543/variable')
        self.cursor = self.conn.connect()
		#Начальное состояние кооманд
        self.cursor.execute("UPDATE State SET value = {} WHERE name = 'start_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name = 'pause_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name = 'stop_model'".format(0))


        
        
    def init(self,name):
	#Открытие модели по имени
        res_filename = self.cursor.execute("""SELECT filename FROM Modelselection WHERE Name='{}'""".format(name))
        for row in res_filename:
            file_name = row['filename']
        subprocess.Popen(r'c:\SimInTech64\bin\mmain.exe  "..\..\model-web-app\restmodel\simintech\modbus_control\modbus_control.prt" /setparameter COMMAND_file_name {} /nomainform /hide /run'.format(file_name), shell = True)

        
		
		
    def write_to_db(self):
	    #Подключение к modbus
        self.master_signal = ModbusTcpClient(host='localhost',port=1503)
		# Создаем два DataFrame для битов и регистров
        registers_dataframe = pd.read_sql("""SELECT number,id FROM variable WHERE type='registers' ORDER BY number""", self.conn)
        bits_dataframe = pd.read_sql("""SELECT number,id FROM variable WHERE type='bits' ORDER BY number""", self.conn, columns=['number', 'variable_id'])
        # Переименовываем колонки
        bits_dataframe.columns = ['number', 'variable_id']
        registers_dataframe.columns = ['number', 'variable_id']
		#Считывание id архива
        res_id = self.cursor.execute(""" SELECT id FROM Achive ORDER BY id DESC LIMIT 1""")
        for row in res_id:
            achive_id = row['id']
        # Заполняем колонку achive_id
        bits_dataframe['achive_id'] = achive_id
        registers_dataframe['achive_id'] = achive_id
        # Максимальное число регистров и битов, читаемых за один запрос
        reg_count = registers_dataframe.shape[0]*2
        bit_count = bits_dataframe.shape[0]
        max_reg = 125
        max_bit = 2000
        first_time = True
		
        current_time = datetime.datetime.now()
        while True:
            start_time = time.time()
	    #Опрос базы данных на значение работы проекта
            res_run = self.cursor.execute("SELECT value FROM State WHERE id = 1")
            for row in res_run:
                run = row['value']
				
            if run != True:
               break
			   
            else:
                reg_data = []
                for start in range(0,reg_count,max_reg):
                    number = min(reg_count-start, max_reg)
                    request = self.master_signal.read_holding_registers(start, number, unit=1)
                    result = request.registers
                    reg_data += result
                reg_data = np.array(reg_data, dtype=np.int16).view(dtype = np.float32)
				
                bit_data = []
                for start in range(0, bit_count, max_bit):
                    number = min(bit_count-start, max_bit)
                    request = self.master_signal.read_coils(start, number, unit=1)
                    result = request.bits
                    bit_data += result
                
				#Время из модели
                time_data = []
                request = self.master_signal.read_holding_registers(reg_count, 2, unit=1)
                result = request.registers
                time_data += result
                time_data = np.array(time_data, dtype=np.int16).view(dtype = np.float32)
                #Преобразование к нужному формату
                hour_time = int(time_data // 3600)
                minute_time = int(time_data // 60)
                second_time = int(time_data % 60)
                
                # Запись времени в DataFrame 
                
                bits_dataframe['time'] = current_time + timedelta(0,second_time,0,0,minute_time,hour_time,0)
                registers_dataframe['time'] = current_time + timedelta(0,second_time,0,0,minute_time,hour_time,0)
    
                # Запись новых значений в DataFrame
                bits_dataframe['value'] = np.array(bit_data[:bit_count], dtype=np.int16)
                registers_dataframe['value'] = reg_data
    
                # Проверка значений на изменение
                if first_time:
                    bits_dataframe['for_DB'] = True
                    registers_dataframe['for_DB'] = True
                    first_time = False
                else:
                    bits_dataframe['for_DB'] = bits_dataframe['value'] !=  bits_dataframe['old_value']
                    registers_dataframe['for_DB'] = abs(registers_dataframe['value'] - registers_dataframe['old_value']) / np.maximum(abs(registers_dataframe['value']), 1e-9) > 0.001
    
                # Запись старых значений в DataFrame
                bits_dataframe['old_value'] = bits_dataframe['value']
                registers_dataframe['old_value'] = registers_dataframe['value']
    
                # Запись данных в базу
                bits_dataframe[['value', 'achive_id', 'variable_id', 'time']][bits_dataframe['for_DB']].to_sql('signals', self.conn, if_exists='append', index=False, method='multi')
                registers_dataframe[['value', 'achive_id', 'variable_id', 'time']][registers_dataframe['for_DB']].to_sql('measurement', self.conn, if_exists='append', index=False, method='multi')
    
                time.sleep(max(0, 1 + start_time - time.time()))
        
				
				
    def create_model(self,name):
        res_id = self.cursor.execute("""SELECT id FROM Modelselection WHERE Name='{}'""".format(name))
        #model_id= self.cursor.fetchone()[0]
        for row in res_id:
            model_id = row['id']
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
        for i in range(0,len(fd)+1):
            self.cursor.execute("""INSERT INTO Variable (name,type,number,max_value,min_value,model_id) VALUES ('{}','registers','{}','10000','0','{}')""".format(fd[i],i*2,model_id))
            #self.conn.commit()
        gd = g.readlines()
        for i in range(0,len(gd)+1):
            gd[i]=list(gd[i])
            for j in range(0,len(gd[i])):
                if gd[i][j] == '\n':
                    gd[i][j] = '' 
            gd[i] = "".join(gd[i])
        res_id = self.cursor.execute(""" SELECT id FROM Variable ORDER BY id DESC LIMIT 1""")
        for row in res_id:
            id = row['id']
        for i in range(0,len(gd)):
            self.cursor.execute("""INSERT INTO Variable (id,name,type,number,max_value,min_value,model_id) VALUES ('{}','{}','bits','{}','1','0','{}')""".format(id+i+1,gd[i],i,model_id))
            #self.conn.commit()
    
    def variable_to_dash(self):
        res_bits = self.cursor.execute(""" SELECT number FROM Variable ORDER BY id DESC LIMIT 1""")
        for row in res_bits:
            size_bits = row['number']
        res_id_next = self.cursor.execute(""" SELECT id FROM Variable ORDER BY id DESC LIMIT 1""")
        for row in res_id_next:
            id_next = row['id']
        id_vals=id_next-size_bits
        res_vals = self.cursor.execute(""" SELECT number FROM Variable WHERE id = {}""".format(id_vals-1))
        for row in res_vals:
            size_vals = row['number']        
        size_vals = int((size_vals+2)/2)
        funct = pd.read_sql("""SELECT * FROM Variable ORDER BY id DESC LIMIT {}""".format(size_bits+size_vals),self.conn)
        funct_name = funct['name'].values
        funct_id = funct['id'].values
        string = ''
        for i in range(len(funct_name)):
            string += funct_name[i] + ','
        for i in range(len(funct_id)):
            string += '{}'.format(funct_id[i]) + ',' 
        return string
		
    def build_graph(self,id):
        res_id = self.cursor.execute(""" SELECT id FROM Achive ORDER BY id DESC LIMIT 1""")
        for row in res_id:
            achive_id = row['id']
        res_type = self.cursor.execute("""SELECT type from variable WHERE id = {} """.format(id))
        for row in res_type:
            type_ = row['type']
        if type_ == 'bits':
            funct = pd.read_sql("SELECT * from Signals WHERE variable_id = {} and achive_id = {}".format(id,achive_id),self.conn)
        if type_ == 'registers':
            funct = pd.read_sql("SELECT * from Measurement WHERE variable_id = {} and achive_id = {}".format(id,achive_id),self.conn) 
        funct_time = funct['time'].values
        funct_value = funct['value'].values
        string = ''
        for i in range(len(funct_time)):
            string += '{}'.format(funct_time[i]) + ','
        for i in range(len(funct_value)):
            string += '{}'.format(funct_value[i]) + ',' 
        return string
		
	    
		
    def start(self):
	#Передача по ТСР команды старт
        self.master_control.execute(1, cst.WRITE_MULTIPLE_REGISTERS,6,output_value=[0,16256])
        time.sleep(10)
	#Передача в базу данных значений состояния проекта
        self.cursor.execute("UPDATE State SET value = {} WHERE name='start_model'".format(1))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='pause_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='stop_model'".format(0))
        #self.conn.commit()
	#Создание архива
        if self.pause != True:
            self.cursor.execute("""INSERT INTO Achive (datetime) VALUES ('{}')""".format(datetime.datetime.now()))
        p_1 = Process(target=self.write_to_db())
        p_1.start()
        self.write_to_db()
	
    def pause(self):
	#Передача по ТСР команды пауза
        self.pause = True
        self.master_control.execute(1,cst.WRITE_MULTIPLE_REGISTERS,0,output_value=[0,16256])
	#Передача в базу данных значений состояния проекта
        self.cursor.execute("UPDATE State SET value = {} WHERE name='start_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='pause_model'".format(1))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='stop_model'".format(0))
       
	
    def stop(self):
	#Передача по ТСР команды стоп
        self.pause = False
	#Передача в SimInTech по модбас команды стоп
        self.cursor.execute("UPDATE State SET value = {} WHERE name='start_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='pause_model'".format(0))
        self.cursor.execute("UPDATE State SET value = {} WHERE name='stop_model'".format(1))
        
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
        
		

	
	
		

if __name__ == '__main__':
    app.run(debug=True)