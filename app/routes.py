"""
Модуль routes.

Модуль для описания REST API.
"""

import asyncio
from quart import jsonify, request
from app import app
from app.simulation import Simulation, add_variables
from pymodbus.client.asynchronous.tcp \
     import AsyncModbusTCPClient as ModbusClient
from pymodbus.client.asynchronous import schedulers
from threading import Thread

from app.restarts_handler \
     import clear_temp_restarts, show_restarts_list, \
     restarts_handler, rewrite_restart

import time
import os

from app import db
from app.models import Measurementvariable, Signalvariable, Model

sim = Simulation()


async def run_modbus_loop(port, message, func, *args):
    """
    Функция запуска modbus.

    Фунция добавляет modbus в цикл событий.
    """
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


@app.route('/', methods=['GET'])
async def hello():
    """
    Функция для отображения описания REST API.

    Перечисляются все методы REST API.
    """
    return 'Привет'


@app.route('/simulation', methods=['GET'])
async def get_simulation():
    """
    Информация о процессе моделирования.

    Функция выдает данные оп процессе моделирования.
    """
    return jsonify(sim.simulation)


@app.route('/simulation/start/<string:model_name>', methods=['PUT'])
async def start_SIT(model_name):
    """
    Запуск SimInTech.

    Функция запускает программу SimInTech.
    """

    async def step_by_step():
        await sim.start_SIT(model_name)
        print('SimInTech запущен!')
        await run_modbus_loop(sim.modbus_control_port,
                              "Обновление статуса остановлено",
                              sim.reading_model_status)
        print('Обновление статуса запущено ...')

    if sim.simulation['status'] == "SimInTech is not running":
        asyncio.ensure_future(step_by_step())
        return f'Запуск SimInTech с моделью {model_name} ...'
    else:
        return f"SimInTech уже запущен с моделью {sim.simulation['model']['name']}"


@app.route('/simulation/stop', methods=['PUT'])
async def kill_SIT():
    """
    Остановить моделирование.

    Функция закрывает программу SimInTech.
    """
    if sim.simulation['status'] == "SimInTech started":
        sim.kill_SIT()
        return 'SimInTech остановлен'
    else:
        return 'SimInTech не запущен'


@app.route('/simulation/start_status_loop', methods=['PUT'])
async def start_status_loop():
    """
    Обновление статуса модели.

    Функция запускает цикл обновления информации о статусе запущенной
    в SimInTech модели
    """
    await run_modbus_loop(sim.modbus_control_port,
                          "Обновление статуса остановлено",
                          sim.reading_model_status)
    return 'Обновление статуса запущено ...'


@app.route('/simulation/model/start', methods=['PUT'])
async def start_model():
    """
    Запуск модели в SimInTech.

    Функция запускает модель.
    """

    async def check_model_start():
        while sim.simulation['model']['status'] != 'started':
            await asyncio.sleep(0.5)

    async def step_by_step():
        await run_modbus_loop(sim.modbus_control_port,
                              "Отправлена команда на запуск модели",
                              sim.change_model_status, 2, True)
        print('Отправлена команда на запуск модели')
        await check_model_start()
        print('Модель запущена!')
        await run_modbus_loop(sim.modbus_model_port,
                              "Запуск чтения данных из модели",
                              sim.reading_model_data)
        print('Чтение данных из модели ...')

    if sim.simulation['status'] == "SimInTech started":

        asyncio.ensure_future(step_by_step())
        return 'Модель запущена с чтением данных'
    else:
        return 'SimInTech не запущен'


@app.route('/simulation/model/stop', methods=['PUT'])
async def stop_model():
    """
    Останов модели.

    Функция останавливает модель в SimInTech
    """
    if sim.simulation['status'] == "SimInTech started":
        await run_modbus_loop(sim.modbus_control_port,
                              "Отправлена команда на останов модели",
                              sim.change_model_status, 1, True)
        return 'Отправлена команда на останов модели'
    else:
        return 'SimInTech не запущен'


@app.route('/simulation/model/pause', methods=['PUT'])
async def pause_model():
    """
    Постановка модели на паузу.

    Функция ставит модель в SimInTech на паузу
    """
    if sim.simulation['status'] == "SimInTech started":
        await run_modbus_loop(sim.modbus_control_port,
                              "Отправлена команда постановки модели на паузу",
                              sim.change_model_status, 0, True)
        return 'Отправлена команда постановки модели на паузу'
    else:
        return 'SimInTech не запущен'


@app.route('/simulation/model/restart/save', methods=['POST'])
async def save_restart():
    """
    Сохранение рестарта.

    Функция сохраняет рестарт модели в SimInTech.
    """
    if sim.simulation['status'] == "SimInTech started" \
       and (sim.simulation['model']['status'] == "started"
            or sim.simulation['model']['status'] == "paused"):
        paths = list(set([os.path.join(os.path.dirname(d), 'restarts')
                     for d in sim.simulation['model']['list_of_projects']]))
        asyncio.ensure_future(restarts_handler(sim.simulation['model']['name'],
                                               paths, time.time()))
        await run_modbus_loop(sim.modbus_control_port,
                              "Отправлена команда сохранения рестарта",
                              sim.change_model_status, 3, True)
        return 'Отправлена команда сохранения рестарта'
    else:
        return 'SimInTech не запущен или модель остановлена'


@app.route('/simulation/model/restart/clear_temp', methods=['PUT'])
def restart_clear_temp():
    """
    Удаление временных рестартов.

    Функция удаляет все папки temp_restrts.
    """
    clear_temp_restarts()
    return 'Папка "temp_restarts" удалена!'


@app.route('/simulation/model/restarts', methods=['GET'])
def show_restarts():
    """
    Показать сохраненные рестарты.

    Функция отображает перечень рестартов из папки restrts.
    """
    restarts = show_restarts_list(
                   [os.path.join(os.path.dirname(d), 'restarts')
                    for d in sim.simulation['model']['list_of_projects']])

    return jsonify(restarts)


@app.route('/simulation/model/temp_restarts', methods=['GET'])
def show_temp_restarts():
    """
    Показать временные рестарты.

    Функция отображает перечень рестартов из папки show_temp_restarts
    """
    temp_restarts = show_restarts_list(
                        [os.path.join(os.path.dirname(d), 'temp_restarts')
                         for d in sim.simulation['model']['list_of_projects']])

    return jsonify(temp_restarts)


@app.route('/simulation/model/restart/<string:restart_name>/start',
           methods=['PUT'])
async def start_restart(restart_name):
    """
    Запуск рестарта.

    Функция запускает рестарт с заданным именем.
    """
    paths = [os.path.dirname(d)
             for d in sim.simulation['model']['list_of_projects']]
    restart_name = f'{restart_name}.rst'
    overwritten = await rewrite_restart(paths, restart_name, 'restart.rst')

    return f'Рестарт {restart_name} запущен'


@app.route('/simulation/model/restart/<string:restart_name>/rewrite',
           methods=['POST'])
async def rest_rewrite_restart(restart_name):
    """
    Сохранение рестарта под новым именем.

    Функция сохраняет рестарт под новым именем.
    """
    new_name = request.args.get('new_name')

    return f'Рестарт {restart_name} перезаписан как {new_name}'


@app.route('/model', methods=['GET', 'POST'])
async def get_models():
    """
    Список доступных моделей

    Функция выдает список моделей из базы данных.
    Пример json
    {
        "description": "Модель котла с системой пара СН",
        "filename": "..\\..\\..\\tpp-simulator\\pac\\boiler_model_auxsteam.pak",
        "name": "boiler_model"
    }
    """
    if request.method == 'POST':
        model = await request.get_json()

        db.session.add(Model(**model))
        db.session.commit()

        return model
    else:
        return jsonify([item.serialize for item in Model.query.all()])


@app.route('/model/<string:id>', methods=['GET'])
def get_model(id):
    return jsonify(Model.query.filter_by(id=int(id)).first().serialize)


@app.route('/model/<string:id>/variables', methods=['POST'])
async def add_variable(id):
    """
    {
	   "csv_file":"..\\..\\tpp-simulator\\modbus_signal\\variables.csv"
    }
    """
    csv_file = await request.get_json()
    add_variables(model_id=id, **csv_file)
    return 'Переменные добавлены'

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
