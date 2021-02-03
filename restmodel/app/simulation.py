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

import psutil
import win32gui
import win32process

import re

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

def enum_window_callback(hwnd, args):
    tid, current_pid = win32process.GetWindowThreadProcessId(hwnd)
    if args[0] == current_pid and win32gui.IsWindowVisible(hwnd):
        args[1].append(win32gui.GetWindowText(hwnd))

class Simulation():

    def __init__(self):

        self.SIT_start_pattern = r'c:\SimInTech64\bin\mmain.exe  ".\simintech\modbus_control\modbus_control.prt" /setparameter COMMAND_file_name {} /nomainform /hide /run'

        self.simulation = {}

        self.simulation['status'] = "SimInTech is not running"
        self.simulation['status_update_time'] = 1
        self.simulation['model'] = {}
        self.simulation['model']['name'] = ""
        self.simulation['model']['status'] = ""
        self.simulation['model']['signals_update_time'] = 1
        self.simulation['model']['list_of_projects'] = []

        self.simulation['model']['measurement_names'] = {}
        self.simulation['model']['measurement_values'] = []

        self.simulation['model']['signal_names'] = {}
        self.simulation['model']['signal_values'] = []
        # Настройки Modbus
        self.modbus_host = "127.0.0.1"
        self.modbus_control_port = 1502
        self.modbus_model_port = 1503


    async def start_SIT(self, model_name:str):

        self.simulation['status'] = "SimInTech starts..."
        self.simulation['model']['name'] = model_name


        self.model_filename = Model.query.filter_by(name=model_name).first().filename
        model_id = Model.query.filter_by(name=model_name).first().id

        # Число измерений
        self.measurements_count = Measurementvariable.query.filter_by(model_id=model_id).count()
        # Перечень измерений
        self.simulation['model']['measurement_names'] = {i.name:i.register_number for i in Measurementvariable.query.filter_by(model_id=model_id).all()}

        # Число сигналов для чтения (статус задвижек, механизмов, регуляторов)
        self.signals_count = Signalvariable.query.filter_by(model_id=model_id).count()
        # Перечень сигналов
        self.simulation['model']['signal_names'] = {i.name:i.register_number for i in Signalvariable.query.filter_by(model_id=model_id).all()}


        self.reading_measurements = []
        self.reading_signals = []

        # Запуск SimInTech
        self.model_process = Popen(self.SIT_start_pattern.format(self.model_filename), stdout=PIPE, shell=True)

        # Дальше запускаем проверку окна "О программе". После его закрытия считаем что SIT запущен
        start_check = False
        while True:
            await asyncio.sleep(2)
            windows = []

            if psutil.Process(self.model_process.pid).children():
                win32gui.EnumWindows(enum_window_callback, [psutil.Process(self.model_process.pid).children()[0].pid, windows])

            if not start_check:
                start_check = 'О программе' in windows
                continue

            if 'О программе' not in windows:
                break

        self.simulation['status'] = "SimInTech started"

        # Получаем список запущенных проектов SimInTech
        pattern =  re.compile('C:.*prt')
        self.simulation['model']['list_of_projects'] = [s for s in windows if pattern.match(s)]


    def kill_SIT(self):
        self.simulation['status'] = "SimInTech stops"
        p = Popen("TASKKILL /F /PID {pid} /T".format(pid=self.model_process.pid))

        self.simulation['status'] = "SimInTech is not running"
        self.simulation['model']['name'] = ""
        self.simulation['model']['status'] = ""

    def restart_model(self):
        pass

    def update_data(self):
        pass

    def connect_to_control_modbus(self):
        pass

    def connect_to_model_modbus(self):
        pass

    async def reading_model_status(self, client):
        while self.simulation['status'] == "SimInTech started":
            rr = await client.read_coils(0, 8, unit=1)
            status = rr.bits

            if status[5] and not status[6] and not status[7]:
                self.simulation['model']['status'] = "started"
            elif not status[5] and status[6] and not status[7]:
                self.simulation['model']['status'] = "paused"
            elif not status[5] and not status[6] and status[7]:
                self.simulation['model']['status'] = "stoped"
            else:
                self.simulation['model']['status'] = "indefined"

            await asyncio.sleep(self.simulation['status_update_time'])


    async def change_model_status(self, client, bit_nmb, bit_val):
        rq = await client.write_coil(bit_nmb, bit_val, unit=1)



    async def reading_model_data(self, client):
        max_reg = 125 # максимально число считываемых за раз регистров
        max_bit = 2000

        reading_reg = []
        reading_bit = []

        reg_count = self.measurements_count * 2
        bit_count = self.signals_count
        bit_count = 3000

        for start in range(0,reg_count,max_reg):
            number = min(reg_count-start, max_reg)
            rr = await client.read_holding_registers(start, number, unit=1)
            reading_reg += rr.registers

        for start in range(0,bit_count,max_bit):
            number = min(bit_count-start, max_bit)
            rr = await client.read_coils(start, number, unit=1)
            print("start {}".format(start))
            reading_bit += rr.bits
            print("норм")

        self.reading_measurements = np.array(reading_reg, dtype=np.int16).view(dtype = np.float32)

        print(reading_reg[0:10])
        print(reading_bit[0:10])
        self.reading_signals = reading_bit



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
