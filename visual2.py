import os
import time
from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Store the last update time
last_update_time = 0

# Read and parse the data
def parse_data():
    global last_update_time
    times = []
    speeds = []
    prev_time_point = None
    
    try:
        # Check if file was modified
        new_update_time = os.path.getmtime("resultat.txt")
        if new_update_time == last_update_time:
            return times, speeds  # Return empty if no update
        
        with open("resultat.txt", "r") as file:
            lines = file.readlines()

        for line in lines:
            try:
                time_str, speed_str = line.strip().split()
                time_point = datetime.strptime(time_str, "%H:%M")

                # If there is a previous time point, divide up time intervals evenly
                if prev_time_point is not None:
                    speed_seq = list(map(int, speed_str.split('X')[:-1]))
                    time_diff = (time_point - prev_time_point) / len(speed_seq)
                    for i, speed in enumerate(speed_seq):
                        times.append(prev_time_point + i * time_diff)
                        speeds.append(speed)

                prev_time_point = time_point
            except ValueError:  # Handle incorrectly formatted or content in a line
                print(f"Cannot parse line: {line.strip()}")

        last_update_time = new_update_time  # Update the last update time after successful read
    except FileNotFoundError:  # Handle if the file does not exist
        print("File 'resultat.txt' not found. Waiting for the file to be available...")
    
    return times, speeds

# Initialize the Dash app
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    dcc.Graph(id='live-graph', animate=True),
    dcc.Interval(
        id='graph-update',
        interval=10*1000
    ),
])

@app.callback(Output('live-graph', 'figure'),
              [Input('graph-update', 'n_intervals')])
def update_graph_scatter(n):
    times, speeds = parse_data()
    
    # If no update, keep graph the same
    if not times:
        raise dash.exceptions.PreventUpdate
    
    trace = go.Scatter(
        x=times,
        y=speeds,
        name='Speed over Time',
        mode= 'lines+markers'
    )

    layout = go.Layout(
        title='Speed over Time',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Speed [km/h]'),
        showlegend=True
    )

    return {'data': [trace],'layout' : layout}

if __name__ == '__main__':
    app.run_server(debug=True)
