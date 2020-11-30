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
@app.route('/start_model')
def START():
    print('Кнопка СТАРТ нажата')
    model.start()
    return 'Start'

#Запрос паузы проекта	
@app.route('/pause_model')
def PAUSE():
    print('Кнопка Пауза нажата')
    model.pause()
    return 'Pause'
	
#Запрос остановки проекта
@app.route('/stop_model')        
def STOP():
    print('Кнопка СТОП нажата')
    model.stop()
    return 'Stop'
    


#Запрос сохранения рестарта
@app.route('/save_restart_model')  
def save_restart(): 
    print('Кнопка Сохранить рестарт нажата')
    model.save_restart()
    return 'Save Restart'

#Запрос запуск с рестарта        
@app.route('/read_restart_model')  
def read_restart(): 
    print('Кнопка Открыть рестарт нажата')    
    model.read_restart()
    return 'Read Restart'
	
	
#Запись переменных в базу данных
@app.route('/variable_to_bd/<string:name>',methods = ['GET'])  
def variable_to_bd_model(name): 
    print('Переменные записаны в базу данных')    
    model.create_model(name)
    return 'write variable to bd'

    
#Запрос построения графиков (ось - время)
#@app.route('/build_graph/<id>')
#def build_graph_time(id):
 #   funct = pd.read_sql("SELECT * from Measurement WHERE variable_id = {}".format(id),conn) 
  #  funct_time = funct['time'].values
   # funct_value = funct['value'].values
    #funct = str(funct_time[0:len(funct_time)]) + str(funct_value[0:len(funct_value)]) 
    #return (funct)
	
#Запрос построения графиков (ось - переменная)
#@app.route('/build_graph_value/<id>')
#def build_graph_value(id):
#    funct = pd.read_sql("SELECT * from Measurement WHERE variable_id = {}".format(id),conn) 
#    funct_value = funct['value'].values
#    funct_value = str(funct_value[0:len(funct_value)]) 
#    return (funct_value)

    

	
		

if __name__ == '__main__':
    app.run(debug=True)

