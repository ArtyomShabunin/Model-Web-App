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
from sqlalchemy import create_engine
# from pymodbus.client.sync import ModbusTcpClient

import os
import csv
from subprocess import Popen, PIPE
import asyncio
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
from pymodbus.client.asynchronous import schedulers
import numpy as np

from app import app, db
from app.models import *
# from datetime import timedelta

csv_file = r"..\simintech\model\modbus_signal\variables.csv"
script_dir = os.path.dirname(__file__)

def add_variables(csv_file, model_id):
    abs_file_path = os.path.join(script_dir, csv_file)
    f = open(abs_file_path)
    reader = csv.reader(f)
    for name, modbus_unit, register_nmb in reader:
        if (int(modbus_unit) == 1) or (int(modbus_unit) == 4):
            u = Measurementvariable(name=name, register_number=register_nmb, modbus_unit=modbus_unit, model_id=model_id)
        else:
            u = Signalvariable(name=name, register_number=register_nmb, modbus_unit=modbus_unit, model_id=model_id)

        db.session.add(u)
    db.session.commit()



class Simulation():

    def __init__(self):

        self.SIT_start_pattern = r'c:\SimInTech64\bin\mmain.exe  ".\simintech\modbus_control\modbus_control.prt" /setparameter COMMAND_file_name {} /nomainform /hide /run'

        # Настройки Modbus
        self.modbus_host = "127.0.0.1"
        self.modbus_control_port = 1502
        self.modbus_model_port = 1503

    def model_initialisation(self, model_name:str):

        self.model_filename = Model.query.filter_by(name=model_name).first().filename
        model_id = Model.query.filter_by(name=model_name).first().id

        # Число измерений
        self.measurements_count = Measurementvariable.query.filter_by(model_id=model_id).count()
        # Число сигналов для чтения (статус задвижек, механизмов, регуляторов)
        self.signals_count = Signalvariable.query.filter_by(model_id=model_id).count()
        # # Число измерений для записи (задания регуляторов, ЧРП)
        # self.measurements_count_2 = Measurementvariable.query.filter_by(model_id=model_id).filter_by(modbus_unit=4).count()
        # # Число сигналов для чтения (статус задвижек, механизмов, регуляторов)
        # self.signals_count_2 = Signalvariable.query.filter_by(model_id=model_id).filter_by(modbus_unit=3).count()

        self.reading_measurements = []
        self.reading_signals = []

        # Запуск SimInTech
        self.model_process = Popen(self.SIT_start_pattern.format(self.model_filename), stdout=PIPE, shell=True)
        # Выдержка времени!!!!!!!!!!!!!!!
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

    async def reading_data(self, client):
        max_reg = 125 # максимально число считываемых за раз регистров
        max_bit = 2000

        reading_measurements_reg = []
        reading_signals_reg = []

        meas_reg_count = self.measurements_count * 2
        signals_reg_count = self.signals_count
        signals_reg_count = 3000

        # meas_reg_count = 100
        # signals_reg_count = 200

        for start in range(0,meas_reg_count,max_reg):
            number = min(meas_reg_count-start, max_reg)
            rr = await client.read_holding_registers(start, number, unit=1)
            reading_measurements_reg += rr.registers

        for start in range(0,signals_reg_count,max_bit):
            number = min(signals_reg_count-start, max_bit)
            rr = await client.read_coils(start, number, unit=1)
            print("start {}".format(start))
            reading_signals_reg += rr.bits
            print("норм")

        self.reading_measurements = np.array(reading_measurements_reg, dtype=np.int16).view(dtype = np.float32)

        print(reading_measurements_reg[0:10])
        print(reading_signals_reg[0:10])
        self.reading_signals = reading_signals_reg



    async def start_async_test(self, client):

        reg_count = self.measurements_count * 2
        bit_count = 5475
        max_reg = 125
        max_bit = 2000


        for i in range(10):

            data = []

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
        # loop.run_until_complete(self.start_async_test(client.protocol))
        loop.run_until_complete(self.reading_data(client.protocol))
        loop.close()

if __name__ == '__main__':
    file_name = r"..\..\simintech\model\pac\boiler_model_auxsteam.pak"
    sim = Simulation()
    sim.model_initialisation('boiler_model')
