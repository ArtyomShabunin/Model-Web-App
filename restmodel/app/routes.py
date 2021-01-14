from flask import Flask
from app import app, db
from app.models import *
# from app.model import Model

model = Model()


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
