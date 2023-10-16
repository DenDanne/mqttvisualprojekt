import os
from datetime import datetime, timedelta
import plotly.graph_objs as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

def parse_data():
    times = []
    speeds = []
    prev_time_point = None
    current_day = datetime.now().date()  # Get the current date
    
    try:
        with open("resultat.txt", "rb") as file:
            lines = file.readlines()
            lines = [line.decode('utf-8') for line in lines]

        for line in lines:
            try:
                time_str, speed_str = line.strip().split()
                time_point = datetime.strptime(time_str, "%H:%M")

                # Check if time_point is less than prev_time_point, 
                # implying the day has changed.
                if prev_time_point and time_point < prev_time_point:
                    current_day += timedelta(days=1)
                
                # Combine the current day and time_point to get the full datetime.
                time_point = datetime.combine(current_day, time_point.time())

                if prev_time_point is not None:
                    speed_seq = list(map(int, speed_str.split('X')[:-1]))
                    time_diff = (time_point - prev_time_point) / len(speed_seq)
                    for i, speed in enumerate(speed_seq):
                        times.append(prev_time_point + i * time_diff)
                        speeds.append(speed)

                prev_time_point = time_point
            except ValueError:  
                print(f"Cannot parse line: {line.strip()}")
    except FileNotFoundError:  
        print("File 'resultat.txt' not found. Waiting for the file to be available...")
    
    print(f"Parsed times: {times}")
    print(f"Parsed speeds: {speeds}")
    
    return times, speeds


def count_datapoints():
    try:
        with open("resultat.txt", "r") as file:
            content = file.read()
            return content.count('X')
    except FileNotFoundError:  
        print("File 'resultat.txt' not found. Waiting for the file to be available...")
        return 0

app = dash.Dash(__name__)
app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

app.layout = html.Div(children=[
    dcc.Graph(id='live-graph'),
    html.P(id='data-count', children=[]),
    dcc.Interval(
        id='graph-update',
        interval=5*1000
    ),
    html.Label('Total minutes between every Uplink:'),
    dcc.Slider(
        id='slider',
        min=2,
        max=60,
        step=1,
        marks={i: str(i) for i in range(2, 61)},
        value=2,
    ),
    html.Button('Send Downlink', id='btn-downlink'),
])

@app.callback(Output('live-graph', 'figure'),
              [Input('graph-update', 'n_intervals')])
def update_graph_scatter(n):
    times, speeds = parse_data()
    
    trace = go.Scatter(
        x=times,
        y=speeds,
        name='Speed over Time',
        mode='lines+markers'
    )

    layout = go.Layout(
        title=f'Speed over Time (Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")})',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Speed [km/h]'),
        showlegend=True
    )

    return {'data': [trace],'layout' : layout}

@app.callback(Output('data-count', 'children'),
              [Input('graph-update', 'n_intervals')])
def update_data_count(n):
    count = count_datapoints()
    return f"Total numbers of passages: {count}"

@app.callback(
    Output('btn-downlink', 'n_clicks'),
    Input('btn-downlink', 'n_clicks'),
    State('slider', 'value')
)
def send_downlink(n_clicks, slider_value):
    if n_clicks is not None and n_clicks > 0:
        with open("downlinks.txt", "a") as file:
            file.write(str(slider_value) + "\n")
    return n_clicks

if __name__ == '__main__':
    app.run_server(debug=True)
