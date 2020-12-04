from flask import Flask
from app import app, db
from app.database import *
from app.model import Model

model = Model()




		
#Запрос открытия модели тренажера
@app.route('/run_model/<string:name>',methods = ['GET'])
def INITMODEL(name):
    print('Кнопка ОТКРЫТЬ нажата')
    model.init(name)
    return 'Run'

	
#Запрос запуска проекта
@app.route('/start_model',methods = ['GET'])
def START():
    print('Кнопка СТАРТ нажата')
    model.start()
 

#Запрос паузы проекта	
@app.route('/pause_model',methods = ['GET'])
def PAUSE():
    print('Кнопка Пауза нажата')
    model.pause()
    return 'Pause'
	
#Запрос остановки проекта
@app.route('/stop_model',methods = ['GET'])        
def STOP():
    print('Кнопка СТОП нажата')
    model.stop()
    return 'Stop'
    


#Запрос сохранения рестарта
@app.route('/save_restart_model',methods = ['GET'])  
def save_restart(): 
    print('Кнопка Сохранить рестарт нажата')
    model.save_restart()
    return 'Save Restart'

#Запрос запуск с рестарта        
@app.route('/read_restart_model',methods = ['GET'])  
def read_restart(): 
    print('Кнопка Открыть рестарт нажата')    
    model.read_restart()
    return 'Read Restart'
	
	
#Запись переменных в базу данных
@app.route('/variable_to_bd/<string:name>',methods = ['GET'])  
def variable_to_bd_model(name): 
    print('Переменные записаны в базу данных')    
    model.create_model(name)


#Передача имен переменных в DASH
@app.route('/variable_to_dash', methods = ['GET'])
def variable_to_dash():
    funct = model.variable_to_dash()
    print('Переменные переданы в выпадающий список')
    return funct
	

    
#Запрос построения графиков 
@app.route('/build_graph/<id>')
def build_graph(id):
    funct = model.build_graph(id)
    return funct
	


    

	
		

if __name__ == '__main__':
    app.run(debug=True)

