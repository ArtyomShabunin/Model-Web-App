# from app import app
# import os
# import modbus_tk
# import modbus_tk.defines as cst
# import modbus_tk.modbus_tcp as modbus_tcp
# from threading import Thread
# import time
# import struct
# import pandas as pd
# from multiprocessing import Process
# import numpy as np
# import subprocess
# import datetime
# from sqlalchemy import create_engine
# from pymodbus.client.sync import ModbusTcpClient

import os
from subprocess import Popen, PIPE
# from datetime import timedelta

class Simulation():

    def __init__(self, model_filename:str):
        self.model_filename = model_filename
        self.SIT_start_pattern = r'c:\SimInTech64\bin\mmain.exe  "..\simintech\modbus_control\modbus_control.prt" /setparameter COMMAND_file_name {} /nomainform /hide /run'

        #Подключение к Modbus
        # self.master_control = modbus_tcp.TcpMaster(host='localhost',port=1502)

    def model_initialisation(self):
		# Запуск SimInTech
        self.model_process = Popen(self.SIT_start_pattern.format(self.model_filename), stdout=PIPE, shell=True)
        # Выдержка времени
        self.model_initialised = True

    def kill_model(self):
        p = Popen("TASKKILL /F /PID {pid} /T".format(pid=self.model_process.pid))

        self.model_initialised = False


    # def modelselection(self):
    #     name = self.cursor.execute("""SELECT name FROM Modelselection""")
    #     description  = self.cursor.execute("""SELECT description  FROM Modelselection""")
    #     name_model = []
    #     for row in name:
    #         name_model += row
    #     for row in description:
    #         name_model += row
    #     name_model = str(name_model)
    #     return name_model
