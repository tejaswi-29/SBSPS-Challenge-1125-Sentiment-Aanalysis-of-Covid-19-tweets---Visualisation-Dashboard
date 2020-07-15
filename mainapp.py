import pandas as pd
import dash
import dash_table
import dash_core_components as dcc
import plotly.express as px
import dash_html_components as html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Output,Input
from dash_table.Format import Format
import dash_table.FormatTemplate as FormatTemplate
import datetime
import time
import re
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# from database import df
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
client = Cloudant("USERNAME", "PASSWORD", "URL")
client.connect()
print("connected to db!")
my_database = client['tweets2']
my_document = my_database['Livefeed']
lockdown = my_database['Lockdowns']
#initalising app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)
app.title = 'Tweet Monitor'

df1 = pd.DataFrame()
df2 = pd.DataFrame() 
for i in my_document['Tweets'].values():
    df1 =  df1.append({'Created_at':i[0],'tweet':i[1],'Sentiment':i[2],'Sentiment':i[2]},ignore_index = True)
df1['Created_at'] = pd.to_datetime(df1['Created_at'])

#finding most frequently used words
content = ' '.join(df1["tweet"])
content = re.sub(r"http\S+", "", content)
content = content.replace('RT ', ' ').replace('&amp;', 'and')
content = re.sub('[^A-Za-z0-9]+', ' ', content)
content = content.lower()
content = content.replace("july", ' ')
content = content.replace("covid",' ')
tokenized_word = word_tokenize(content)
stop_words=set(stopwords.words("english"))
filtered_sent=[]
for w in tokenized_word:
    if w not in stop_words:
        filtered_sent.append(w)
fdist = FreqDist(filtered_sent)
fd = pd.DataFrame(fdist.most_common(10),columns = ["Word","Frequency"]).drop([0]).reindex()



#counting negatives and positives and neutrals:
slist = df1['Sentiment'].tolist()
positive=0
negative=0
neutral=0
for i in slist:
    if i<0:
        negative+=1
    elif i>0:
        positive+=1
    else:
        neutral+=1
polaritycounts = [positive,negative,neutral]
polaritynames = ["Positive Tweets","Negative Tweets","Neutral Tweets"]

#getting the data table
def get_data_table():
    table = pd.DataFrame()
    table['Tweet']=df1['tweet']
    table['Sentiment']=df1['Sentiment']
    data_table = dash_table.DataTable(
        id = 'datatable-data',
        columns = [{'name':c,'id':c} for c in table.columns],
        data = table.to_dict('records'),
        page_current = 0,
        page_size = 20,
        style_as_list_view=True,
        style_header={'backgroundColor': 'rgb(30, 30, 30)',
                      'width':30,
                      'textAlign': 'center'},
        style_cell={
        'backgroundColor': 'rgb(50, 50, 50)',
        'color': 'white'
     },
        style_table={
                             'height': 'auto',
                             'overflowX': 'auto',
                             'width':'auto'
        },
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        
    )
    return data_table
#creating graphs:
y=[my_document['Joy'],my_document['Sadness'],my_document['Tentative'],my_document['Analytical'],my_document['Fear'],
        my_document['Confident'],my_document['Anger'],my_document['Neutral']]
graphs = make_subplots(rows=1,cols=2,
                       subplot_titles=("Count of the emotions of the tweets during each lockdown","Score of each emotion in each of the lockdowns"))
graphs1 = make_subplots(rows=1,cols=2,subplot_titles=("Live count of emotions of the tweets","Words most frequently used"))
graphs1.update_layout(height=600,template="plotly_dark")
trace1 = go.Bar(
    x=['Joy','Sadness','Tentative','Analytical','Fear','Confident','Anger','Neutral'],
    y=y,
    text = y,
    textposition = 'outside'
)
graphs1.append_trace(trace1,1,1)
trace2  = go.Bar(
    y=fd["Frequency"].loc[::-1],
    x=fd["Word"].loc[::-1], 
    orientation='v'
    )
graphs1.append_trace(trace2,1,2)
l1 =go.Scatter(
    x=['Joy','Sadness','Tentative','Analytical','Fear','Confident','Anger'],
    y=[314.877,79.450,175.787,238.881,11.576,144.614,5.759]
)
l1count = go.Scatter(
    y = [v for v in lockdown['Lockdown1'].values()],
    x = [v for v in lockdown['Lockdown1']]
)
l2 = go.Scatter(
    x=['Joy','Sadness','Tentative','Analytical','Fear','Confident','Anger'],
    y=[215.541,72.755,141.158,196.285,9.922,96.045,6.924],
)
l2count = go.Scatter(
    y = [v for v in lockdown['Lockdown2'].values()],
    x = [v for v in lockdown['Lockdown2']]
)
l3 = go.Scatter(
    x=['Joy','Sadness','Tentative','Analytical','Fear','Confident','Anger'],
    y=[180.970,120.723,174.059,215.677,10.581,87.614,12.564]
    )
l3count = go.Scatter(
    y = [v for v in lockdown['Lockdown3'].values()],
    x = [v for v in lockdown['Lockdown3']]
)
l4 = go.Scatter(
    x = ['Joy','Sadness','Tentative','Analytical','Fear','Confident','Anger'],
    y = [153.572,85.073,154.209,213.389,9.925,106.957,5.418]
)
l4count = go.Scatter(
    y = [v for v in lockdown['Lockdown4'].values()],
    x = [v for v in lockdown['Lockdown4']]
)
l5 = go.Scatter(
    x = ['Joy','Sadness','Tentative','Analytical','Fear','Confident','Anger'],
    y = [219.869,79.320,132.351,192.129,9.346,94.883,11.068]
)
l5count = go.Scatter(
    y = [v for v in lockdown['Lockdown5'].values()],
    x = [v for v in lockdown['Lockdown5']],
)

app.layout = html.Div(
     [
    html.H1('Sentiment Analysis of Covid Tweets',
    style={
        'textAlign':'center',
        'background': 'white'
    }
    ),
    html.H5('Currently tracking "#covid19inindia" on Twitter',
            style={
                'textAlign':'center',
                'background':'white'
                }),
    
    html.Div([
        # dcc.Input(id='sentiment_term',value='#covid19hyd',type='text'),
        dcc.Graph(
        id ='graph-1',
        animate=True,
        figure={
           
            'data':[
                 go.Scatter(
                x=df1['Created_at'],
                y=df1['Sentiment']
            )
            ],
            'layout':{
                'title':'Tweet Sentiments',
                'hovermode':"closest",
                'xaxis_title':"Created at",
                'yaxis_title':"Sentiment score"
            }
        }
    )
        
        #  dcc.Interval(
        #     id='graph-update',
        #     interval=1*1000,
        #     n_intervals=0
        # )
   ]),
     dcc.Graph(
      figure=graphs1,id='graph2n3'  
    ),
    dcc.Graph(
        id = 'donut',
        figure={
            'data':[
                go.Pie(labels=polaritynames,
                       values=polaritycounts,
                       hole=0.50,name='View Metrics!',
                       marker_colors = ['rgba(255, 50, 50, 0.6)','rgba(184, 247, 212, 0.6)','rgba(131, 90, 241, 0.6)']),
            ]
        }
    ),
    
    html.Div(children = [
    dcc.Dropdown(
            id= 'dropdown',
            options=[
                {'label': 'Lockdown1', 'value': 'lockdown1'},
                {'label': 'Lockdown2', 'value': 'lockdown2'},
                {'label': 'Lockdown3', 'value': 'lockdown3'},
                {'label': 'Lockdown4', 'value': 'lockdown4'},
                {'label': 'Lockdown5', 'value': 'lockdown5'},
            ]
    ),
    
    dcc.Graph(
        figure=graphs,id='graph4'
    )]),
    html.Div(children=[html.H1(children="Live Tweets", # html for table
                        style={
                        'textAlign': 'center',
                        "background": "white",
                        'font-size':60
                        }),
                        get_data_table()])
    
], style = {
    'background':'#000080'
}
)
# if value=='None':

@app.callback(
    dash.dependencies.Output('graph4', 'figure'),
    [dash.dependencies.Input('dropdown', 'value')])

def display_graphs(value):
    
    if value=='lockdown1':
        graphs.append_trace(l1,1,2)
        graphs.append_trace(l1count,1,1)
    if value=='lockdown2':
        graphs.append_trace(l2,1,2)
        graphs.append_trace(l2count,1,1)
    if value == 'lockdown3':
        graphs.append_trace(l3,1,2)
        graphs.append_trace(l3count,1,1)
    if value == 'lockdown4':
        graphs.append_trace(l4,1,2)
        graphs.append_trace(l4count,1,1)
    if value == 'lockdown5':
        graphs.append_trace(l5,1,2)
        graphs.append_trace(l5count,1,1)
    
    graphs['layout'].update(height=600,template="plotly_dark")
    return graphs      
#Running the app

if __name__ == '__main__':
    app.run_server(debug=True)