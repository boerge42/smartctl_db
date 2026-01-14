# *********************************************************************************************
#
#    graphs.py
# ----------------
# Uwe Berger; 2025
#
# Diagramme für web_smartctl
#
# ---------
# Have fun!
#
# *********************************************************************************************

from plotly.offline import plot
import plotly.graph_objs as go

# ***********************************************************************
def generate_line_graph(data, computer, device_name, generation, value_name, description):

    # Daten transformieren (datetimes/values)
    datetimes = []
    values = []
    for d in data:
        datetimes.append(d.timestamp)
        if isinstance(d.value, (str)):
            v = int(d.value)
        else:
            v = d.value
        values.append(v)

    # Liniendiagramm
    trace = go.Scatter(
        x=datetimes,
        y=values,
        mode='lines+markers', # lines|markers|text?
        name='',
        line_shape="linear", # linear|spline
        hovertemplate='timestamp: %{x}<br>value: %{y:.0f}'
    )

    if description is not None:
        value_name = f"{value_name} ({description})"
    layout = go.Layout(
        title=f"{computer} -> {device_name} ({generation})<br><b>{value_name}</b>",
        title_x = 0.5,
        xaxis=dict(title='date/time'),
        yaxis=dict(title='value', 
                   autorange=True,
                   #tickformat='.0f'
                   ),
        height=700
    )

    fig = go.Figure(data=[trace], layout=layout)

    # als html-div zurückgeben
    return plot(fig, output_type='div')
