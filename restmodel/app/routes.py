import asyncio
from quart import Quart, jsonify
from app import app, db
from app.models import *
from app.simulation import Simulation
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
from pymodbus.client.asynchronous import schedulers
from threading import Thread

from app.restarts_handler import watch_restarts, clear_temp_restarts, show_restarts_list, RestartsHandler

from app.new_restarts_handler import consume, RestartsWatcher, make_restart_copy

import time
import os

from pathlib import Path

sim = Simulation()
rw = RestartsWatcher()

async def run_modbus_loop(port, message, func, *args):
    def done(future):
        print(message)
    def start_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()
    loop = asyncio.new_event_loop()
    t = Thread(target=start_loop, args=[loop])
    t.daemon = True
    # Start the loop
    t.start()
    assert loop.is_running()
    asyncio.set_event_loop(loop)

    loop, client = ModbusClient(schedulers.ASYNC_IO, port=port, loop=loop)

    args = (client.protocol, *args)
    future = asyncio.run_coroutine_threadsafe(func(*args), loop=loop)

    future.add_done_callback(done)
    # while not future.done():
    #     time.sleep(0.1)
    # loop.stop()

@app.route('/simulation/model/restarts/start_restarts_handler_2',methods = ['PUT'])
async def start_restarts_handler_2():
    # def done(future):
    #     print("Hello")
    # def start_loop(loop):
    #     asyncio.set_event_loop(loop)
        # loop.run_forever()
    # loop = asyncio.new_event_loop()
    loop = asyncio.get_event_loop()
    # t = Thread(target=start_loop, args=[loop])
    # t.daemon = True
    # # Start the loop
    # t.start()
    # assert loop.is_running()
    # asyncio.set_event_loop(loop)

    async def while_loop(rw, paths):
        while True:
            if time.time() - rw.handler.prev_time < 10:
                await asyncio.sleep(1)
            else:
                print("Простой обсервера больше 10 сек")

                print(f'Длина rw.handler.activ_paths - {len(rw.handler.activ_paths)}')
                print(f'Длина paths - {len(paths)}')




                for path in rw.handler.activ_paths:
                    print(f'path - {path}')
                    print("Очистка списка директорий")
                    print(paths.pop(paths.index(path)))
                    print(f'Длина списка директорий: {len(paths)}')

                if not paths:
                    print("Список директорий пуст")

                    for path in rw.handler.activ_paths:
                        await make_restart_copy(sim.simulation['model']['name'], path)





                else:
                    print("Список директорий:")
                    for i in paths:
                        print(i)

                await asyncio.sleep(4)




    paths = list(set([os.path.join(os.path.dirname(d), 'restarts') for d in sim.simulation['model']['list_of_projects']]))

    queue = asyncio.Queue(loop=loop)
    futures = [
        loop.run_in_executor(None, rw.watch, paths, queue, loop, False),
        consume(queue, sim.simulation['model']['name']),
        while_loop(rw, paths)
    ]

    asyncio.ensure_future(asyncio.gather(*futures))
    # loop.run_until_complete(asyncio.gather(*futures))

    # loop, client = ModbusClient(schedulers.ASYNC_IO, port=port, loop=loop)

    # args = (client.protocol, *args)
    # future = asyncio.run_coroutine_threadsafe(func(*args), loop=loop)
    #
    # future.add_done_callback(done)

    return "Обработчик рестартов запущен"

@app.route('/', methods = ['GET'])
async def hello():
    return 'Привет'

@app.route('/simulation',methods = ['GET'])
async def get_simulation():
    return jsonify(sim.simulation)

@app.route('/simulation/start/<string:model_name>',methods = ['PUT'])
async def start_SIT(model_name):

    if sim.simulation['status'] == "SimInTech is not running":
        asyncio.ensure_future(sim.start_SIT(model_name))

        return f'Запуск SimInTech с моделью {model_name} ...'
    else:
        return f"SimInTech уже запущен с моделью {sim.simulation['model']['name']}"

@app.route('/simulation/stop',methods = ['PUT'])
async def kill_SIT():
    if sim.simulation['status'] == "SimInTech started":
        sim.kill_SIT()
        return 'SimInTech остановлен'
    else:
        return 'SimInTech не запущен'

@app.route('/simulation/start_status_loop',methods = ['PUT'])
async def start_status_loop():
    await run_modbus_loop(sim.modbus_control_port, "Обновление статуса остановлено", sim.reading_model_status)
    return 'Обновление статуса запущено ...'

@app.route('/simulation/model/start',methods = ['PUT'])
async def start_model():
    if sim.simulation['status'] == "SimInTech started":
        await run_modbus_loop(sim.modbus_control_port, "Отправлена команда на запуск модели", sim.change_model_status, 2, True)
        return 'Отправлена команда на запуск модели'
    else:
        return 'SimInTech не запущен'

@app.route('/simulation/model/stop',methods = ['PUT'])
async def stop_model():
    if sim.simulation['status'] == "SimInTech started":
        await run_modbus_loop(sim.modbus_control_port, "Отправлена команда на останов модели", sim.change_model_status, 1, True)
        return 'Отправлена команда на останов модели'
    else:
        return 'SimInTech не запущен'

@app.route('/simulation/model/pause',methods = ['PUT'])
async def pause_model():
    if sim.simulation['status'] == "SimInTech started":
        await run_modbus_loop(sim.modbus_control_port, "Отправлена команда постановки модели на паузу", sim.change_model_status, 0, True)
        return 'Отправлена команда постановки модели на паузу'
    else:
        return 'SimInTech не запущен'

@app.route('/simulation/model/restart/start_restarts_handler',methods = ['PUT'])
async def start_restarts_handler():
    asyncio.ensure_future(watch_restarts(sim.simulation['model']['name'], [os.path.join(os.path.dirname(d), 'restarts') for d in sim.simulation['model']['list_of_projects']]))
    return f'Запуск обработчика рестартов модели ...'

@app.route('/simulation/model/restart/save',methods = ['POST'])
async def save_restart():
    if sim.simulation['status'] == "SimInTech started" and (sim.simulation['model']['status'] == "started" or sim.simulation['model']['status'] == "paused"):
        await run_modbus_loop(sim.modbus_control_port, "Отправлена команда сохранения рестарта", sim.change_model_status, 3, True)
        return 'Отправлена команда сохранения рестарта'
    else:
        return 'SimInTech не запущен или модель остановлена'

@app.route('/simulation/model/restart/clear_temp',methods = ['PUT'])
def restart_clear_temp():
    clear_temp_restarts()
    return 'Папка "temp_restarts" удалена!'

@app.route('/simulation/model/restarts',methods = ['GET'])
def show_restarts():
    restarts = show_restarts_list([os.path.join(os.path.dirname(d), 'restarts') for d in sim.simulation['model']['list_of_projects']])

    return jsonify(restarts)

# @app.route('/modelselection',methods = ['GET'])
# def Modelselection():
#     name_model=model.modelselection()
#     return name_model
#
#
# #Запрос открытия модели тренажера
# @app.route('/run_model/<string:name>',methods = ['POST'])
# def INITMODEL(name):
#     print('Кнопка ОТКРЫТЬ нажата')
#     model.init(name)
#     return 'Run'
#
#
# #Запрос запуска проекта
# @app.route('/start_model',methods = ['PUT'])
# def START():
#     print('Кнопка СТАРТ нажата')
#     model.start()
#     return 'Start'
#
#
# #Запрос паузы проекта
# @app.route('/pause_model',methods = ['PUT'])
# def PAUSE():
#     print('Кнопка Пауза нажата')
#     model.pause_model()
#     return 'Pause'
#
# #Запрос остановки проекта
# @app.route('/stop_model',methods = ['PUT'])
# def STOP():
#     print('Кнопка СТОП нажата')
#     model.stop()
#     return 'Stop'
#
#
#
# #Запрос сохранения рестарта
# @app.route('/save_restart_model',methods = ['POST'])
# def save_restart():
#     print('Кнопка Сохранить рестарт нажата')
#     model.save_restart()
#     return 'Save Restart'
#
# #Запрос запуск с рестарта
# @app.route('/read_restart_model',methods = ['PUT'])
# def read_restart():
#     print('Кнопка Открыть рестарт нажата')
#     model.read_restart()
#     return 'Read Restart'
#
#
# #Запись переменных в базу данных
# @app.route('/variable_to_bd/<string:name>',methods = ['POST'])
# def variable_to_bd_model(name):
#     print('Переменные записаны в базу данных')
#     model.create_model(name)
#     return 'Variable to bd'
#
#
# #Передача имен переменных в DASH
# @app.route('/variable', methods = ['GET'])
# def variable():
#     funct = model.variable()
#     print('Переменные переданы в выпадающий список')
#     return funct
#
#
#
# #Запрос построения графиков
# @app.route('/measurement_signals/<id>', methods = ['GET'])
# def build_graph(id):
#     funct = model.measurement_signals(id)
#     return funct








if __name__ == '__main__':
    app.run(debug=True)
