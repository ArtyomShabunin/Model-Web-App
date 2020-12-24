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
import asyncio
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
from pymodbus.client.asynchronous import schedulers
import numpy as np

# from datetime import timedelta

class Simulation():

    def __init__(self, model_filename:str):
        self.model_filename = model_filename
        self.SIT_start_pattern = r'c:\SimInTech64\bin\mmain.exe  "..\simintech\modbus_control\modbus_control.prt" /setparameter COMMAND_file_name {} /nomainform /hide /run'

        #Подключение к Modbus
        self.modbus_host = "127.0.0.1"
        self.modbus_control_port = 1502
        self.modbus_model_port = 1503
        # self.master_control = modbus_tcp.TcpMaster(host='localhost',port=1502)

    def model_initialisation(self):
		# Запуск SimInTech
        self.model_process = Popen(self.SIT_start_pattern.format(self.model_filename), stdout=PIPE, shell=True)
        # Выдержка времени
        self.model_initialised = True

    def kill_model(self):
        p = Popen("TASKKILL /F /PID {pid} /T".format(pid=self.model_process.pid))

        self.model_initialised = False

    def restart_model(self):
        pass

    def start_model(self):
        pass

    def pause_model(self):
        pass

    def start_model(self):
        pass

    def update_data(self):
        pass

    def connect_to_control_modbus(self):
        pass

    def connect_to_model_modbus(self):
        pass

    async def start_async_test(self, client):

        reg_count = 4714
        reg_count = 125
        bit_count = 5475
        max_reg = 125
        max_bit = 2000

        data = []

        for i in range(10):

            for start in range(0,reg_count,max_reg):
                number = min(reg_count-start, max_reg)
                rr = await client.read_holding_registers(start, number, unit=1)

                result = rr.registers
                data += result

            print('Done!')

            await asyncio.sleep(1)

            # print(rr)
            # print(rr.registers)
            print(np.array(data, dtype=np.int16).view(dtype = np.float32))
            print()

    def run_with_no_loop(self):
        """
        ModbusClient Factory creates a loop.
        :return:
        """
        loop, client = ModbusClient(schedulers.ASYNC_IO, port=self.modbus_model_port)
        loop.run_until_complete(self.start_async_test(client.protocol))
        loop.close()

if __name__ == '__main__':
    file_name = r"..\..\simintech\model\pac\boiler_model_auxsteam.pak"
    sim = Simulation(file_name)
    sim.model_initialisation()