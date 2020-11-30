import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from threading import Thread
import struct
import plotly.graph_objs as go
import requests
import numpy as np
import os
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config["suppress_callback_exceptions"] = True


host = 'http://localhost:5000'

#Функция преобразования переменных
def transformation(sequence):
    sequence = list(sequence)
    for i in range(0,len(sequence)):
        if sequence[i] == '\n' or sequence[i] == '[' or sequence[i] == ']':
            sequence[i] = ' '
    str_sequence = "".join(sequence)
    split_sequence = str_sequence.split()
    for i in range(len(split_sequence)):
        split_sequence[i] = float(split_sequence[i])
    array1 = split_sequence[0:int(len(split_sequence)/2)]
    array2 = split_sequence[int(len(split_sequence)/2):len(split_sequence)]
    return array1,array2
    


app.layout = html.Div(children=
	[
		html.Div(
              style={
            'textAlign': 'left',
            'color': '#EA0900'
              },
			children = [
				html.H2("Работа с математической моделью")],
		className = "banner",
	    ),
	    html.Div(
			[
													html.H3("Открытие модели", style = {"textAlign":"left",'color': '#EA0900'}),
																	html.Div(
                                    [daq.StopButton(
                                                            id="my-runtest-button",
                                                            buttonText="Открыть Тест",
															disabled = False,
															size = 130,
                                                            style={
                                                                "display": "flex",
                                                                "justify-content": "left",
                                                                "align-items": "left",
                                                                "paddingBottom": "1%",
															
                                                            },
                                                            
                                                        ),
														html.Div(id='runtest-button-output'),
														daq.StopButton(
                                                            id="my-runmodel-button",
                                                            buttonText="Открыть Модель",
															disabled = False,
															size = 130,
                                                            style={
                                                                "display": "flex",
                                                                "justify-content": "left",
                                                                "align-items": "left",
                                                                "paddingBottom": "1%",
                                                            },
                                                            
                                                        ),
														html.Div(id='runmodel-button-output'),]),
				html.Div(
					[ 
						html.H3("Управление моделью ", style = {"textAlign":"left",'color': '#EA0900'}),
		
						html.Div(
                                    [

                                                html.Div(
                                                    [
                                                    
														daq.StopButton(
                                                            id="my-start-button",
                                                            buttonText="Старт",
															n_clicks = 0,
                                                            style={
                                                                "display": "flex",
                                                                "justify-content": "left",
                                                                "align-items": "left",
                                                                "paddingBottom": "5%",
																"paddingTop": "10%",
																"color": "#007417",
                                                            },
														),
                                                        html.Div(id='start-button-output'), 
														daq.StopButton(
                                                            id="my-pause-button",
                                                            buttonText="Пауза",
                                                            style={
                                                                "display": "flex",
                                                                "justify-content": "left",
                                                                "align-items": "left",
																"paddingBottom": "5%",
                                                            },
                                                            
                                                        ),
													html.Div(id='pause-button-output'),
                                                        
                                                        daq.StopButton(
                                                            id="my-stop-button",
                                                            buttonText="Стоп",
                                                            style={
                                                                "display": "flex",
                                                                "justify-content": "left",
                                                                "align-items": "left",
                                                                "paddingBottom": "5%",
                                                            },
                                                            
                                                        ),
														html.Div(id='stop-button-output'),
                                                        
								html.Div(
                                    [
                                        
										html.Div(
                                            [
                                                daq.Indicator(
                                                    id="start-indicate",
                                                    label="В работе",
													value = False,
                                                    color="#EF553B",
                                                    className="eight columns",
                                                    labelPosition="bottom",
                                                    size=20,
                                                    style={
                                                        "paddingLeft": "0px",
                                                        "paddingRight": "0px",
                                                        "width": "100px",

                                                          },
                                                             )
                                            ],
                                            className="four columns",
                                            style={
                                                "marginLeft": "0px",
                                                "marginRight": "0px"
                                            },
                                        ),
                                        html.Div(
                                            [
                                                daq.Indicator(
                                                    id="pause-indicate",
                                                    label="На паузе",
                                                    value=False,
                                                    color="#EF553B",
                                                    className="eight columns",
                                                    labelPosition="bottom",
                                                    size=20,
                                                    style={
                                                        "paddingLeft": "0px",
                                                        "paddingRight": "0px",
                                                        "width": "100px"
                                                          },
                                                             )
                                            ],
                                            className="four columns",
                                            style={
                                                "marginLeft": "0px",
                                                "marginRight": "0px"
                                            },
                                        ),
                                        html.Div(
                                            [
                                                daq.Indicator(
                                                    id="stop-indicate",
                                                    label="Остановлена",
                                                    value=False,
                                                    color="#EF553B",
                                                    className="eight columns",
                                                    labelPosition="bottom",
                                                    size=20,
                                                    style={
                                                        "paddingLeft": "0px",
                                                        "paddingRight": "0px",
                                                        "width": "100px"
                                                          },
                                                             )
                                            ],
                                            className="four columns",
                                            style={"zIndex": "50"},
                                        ),
                                    ],
                                    className="row",
                                    style={"marginTop": "0%",
                                           "marginBottom": "4%"},
                                ),

													
													
                                                    ],
                                                    className="three columns",
                                                    style={"marginLeft": "1%"},
                                                ),
												
														  
			
				                      html.H3("Управление рестартом", style = {"textAlign":"top",'color': '#EA0900',"marginTop": "-2.8%"}),
																	html.Div(
                                    [

                                                html.Div(
                                                    [
													daq.StopButton(
                                                            id="my-save_restart-button",
                                                            buttonText="Сохранить рестарт",
															size = 150,
                                                            style={
                                                               "display": "flex",
                                                                "justify-content": "right",
                                                                "align-items": "right",
                                                                "paddingBottom": "5%",
																"paddingright": "100%",
                                                            },
                                                            
                                                        ),
													html.Div(id='save_restart-button-output'),
													daq.StopButton(
                                                            id="my-read_restart-button",
                                                            buttonText="Открыть рестарт",
															size = 150,
                                                            style={
                                                               "display": "flex",
                                                                "justify-content": "right",
                                                                "align-items": "right",
                                                                "paddingBottom": "5%",
																"paddingright": "100%",
																
                                                            },
                                                            
                                                        ),
													html.Div(id='read_restart-button-output'),
													
                                                    ],
                                                    className="three columns",
                                                    style={"marginright": "0%"},
                                                ),
												

                                    
									
                        
                                  
					
		                            ]), 
                            
						

                                    
									]),
									

				]),
											
		]),
		  
		
																	html.Div(
                                    [
			html.Div(
                    [
                        html.Div(
                            [ html.H3("Графики функций", style = {"textAlign":"left",'color': '#EA0900',"marginBottom": "0%"}),
							dcc.Dropdown(
        id='dropdown-graph',
        options=[
            {'label': 'X', 'value': 'X'},
            {'label': 'Y', 'value': 'Y'},
            {'label': 'Z', 'value': 'Z'}
        ],
        placeholder="Выберите функцию для построения графика",
    ),
                                                                dcc.Graph(
                                    id="graph-data-1",
                                    style={"height": "254px", "marginBottom": "1%"},
                                    figure={
                                        "data": [
                                            go.Scatter(
                                                x=[],
                                                y=[],
                                                mode="lines+markers",
                                                marker={"size": 6},
                                             

                                            ),
                                        
                                        ],
                                        "layout": go.Layout(
                                            xaxis={
                                                "title": "Время (с)",
                                                "autorange": True,
                                            },
                                            yaxis={"title": "Переменная"},
                                            margin={"l": 70, "b": 20, "t": 10, "r": 25},
                                        ),
                                    },
                                ),
                            ],
                            className="twelve columns",
                            style={
                                "border-radius": "5px",
                                "border-width": "5px",
                                "border": "1px solid rgb(216, 216, 216)",
                                "marginBottom": "2%",
                            },
                        )
                    ],
                    className="row",
                    style={"marginTop": "3%"},
                ),
				]),
	])
	

	
#Кнопка открытия тестовой модели
@app.callback(Output('runtest-button-output','children'),
    [Input('my-runtest-button','n_clicks')])
def RUNTEST(n_clicks):
    if n_clicks:
        requests.get('{}/run_model/TestModel'.format(host))
 
#Кнопка открытия модели тренажера 
@app.callback(Output('runmodel-button-output','children'),
    [Input('my-runmodel-button','n_clicks')])
def RUNMODEL(n_clicks):
    if n_clicks:
        requests.get('{}/run_model/Model'.format(host))
        		
 

#Кнопка старта модели
@app.callback(Output('start-button-output','children'),
 [Input('my-start-button','n_clicks')])
def START(n_clicks):
    if n_clicks:
        requests.get('{}/start_model'.format(host))

	
		



#Кнопка поставить модель на паузу
@app.callback(Output('pause-button-output','children'),
    [Input('my-pause-button','n_clicks')])
def PAUSE(n_clicks): 
    if n_clicks:
        requests.get('{}/pause_model'.format(host))

       
#Кнопка остановить модель
@app.callback(Output('stop-button-output','children'),
   [Input('my-stop-button','n_clicks')])
def STOP(n_clicks):
    if n_clicks:
        requests.get('{}/stop_model'.format(host))

#Выбор переменной из списка для построения графика    
@app.callback(Output('graph-data-1', 'figure'),
[Input('dropdown-graph', 'value')],prevent_initial_call=True)
def build_graph(value):
    if value == 'X':
        id = 2
    elif value == 'Y':
        id = 1
    elif value == 'Z':
        id = 3		
    df = requests.get('{}/build_graph/{}'.format(host,id))
    time_gr,value_gr = transformation(df.text)
    fig = px.scatter( x = time_gr, y = value_gr)
    fig.update_traces(marker_size = 6, line_width = 1, mode = "lines+markers")
    return fig    
        
#Кнопка сохранить рестарт
@app.callback(Output('save_restart-button-output','children'),
    [Input('my-save_restart-button','n_clicks')])
def save_restart(n_clicks): 
    if n_clicks:
        requests.get('{}/save_restart_model'.format(host))
       
#Кнопка открыть модель с рестарта
@app.callback(Output('read_restart-button-output','children'),
   [Input('my-read_restart-button','n_clicks')])
def read_restart(n_clicks): 
    if n_clicks:
        requests.get('{}/read_restart_model'.format(host))

 
if __name__ == "__main__":
    app.run_server(debug=True)
   
