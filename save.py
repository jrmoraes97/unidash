from dash import Dash, html, dcc, Output, Input, callback
import plotly.express as px
import pandas as pd
import json
import requests
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)

# Carregando dados de homicídios
df_uf = pd.read_csv("homic-estados.csv", sep=';', usecols=['nome','ano', 'valor'])
df_uf['nome'] = df_uf['nome'].str.strip()

# Carregando dados de suicídios
df_suic = pd.read_csv("suicidio-de-homens-por-armas-de-fogo.csv", sep=';', usecols=['nome','ano', 'valor'])
df_suic['nome'] = df_suic['nome'].str.strip()

# Carregando homicídios por sexo
df_homens = pd.read_csv("homic-homens.csv", sep=';', usecols=['nome', 'ano', 'valor'])
df_homens['sexo'] = 'Homens'

df_mulheres = pd.read_csv("homic-mulheres.csv", sep=';', usecols=['nome', 'ano', 'valor'])
df_mulheres['sexo'] = 'Mulheres'

df_sexo = pd.concat([df_homens, df_mulheres], ignore_index=True)
df_sexo['nome'] = df_sexo['nome'].str.strip()

# GeoJSON
geojson_url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
geojson_estados = requests.get(geojson_url).json()

siglas = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA',
    'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO',
    'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
    'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI',
    'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS',
    'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP',
    'Sergipe': 'SE', 'Tocantins': 'TO'
}

for feature in geojson_estados['features']:
    nome_estado = feature['properties']['name']
    sigla = siglas.get(nome_estado)
    feature['properties']['sigla'] = sigla

df_uf['sigla'] = df_uf['nome'].map(siglas)

app.layout = dbc.Container([
    html.H2("\ud83d\udcca Análise de Homicídios e Suicídios por Armas de Fogo", className="text-center my-4 text-primary"),

    dcc.Tabs(id="tabs", value='tab-mapa', children=[
        dcc.Tab(label='\ud83d\uddfa\ufe0f Mapa de Homicídios', value='tab-mapa'),
        dcc.Tab(label='\ud83d\udd2b Top Estados Suicídios', value='tab-suicidios'),
        dcc.Tab(label='\ud83d\udc6b Homicídios por Sexo', value='tab-sexo')
    ]),

    html.Div(id='conteudo-abas')
], fluid=True)

@callback(
    Output('conteudo-abas', 'children'),
    Input('tabs', 'value')
)
def renderizar_abas(aba):
    if aba == 'tab-mapa':
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("Ano:"),
                    dcc.Slider(
                        df_uf['ano'].min(),
                        df_uf['ano'].max(),
                        value=df_uf['ano'].min(),
                        marks={str(ano): str(ano) for ano in df_uf['ano'].unique()},
                        step=None,
                        id='anos-homic'
                    )
                ], width=12),
                dbc.Col([
                    dcc.Graph(id='homicidios')
                ], width=12)
            ])
        ])

    elif aba == 'tab-suicidios':
        return dbc.Row([
            dbc.Col([
                html.Label("Ano:"),
                dcc.Slider(
                    df_suic['ano'].min(),
                    df_suic['ano'].max(),
                    value=df_suic['ano'].min(),
                    marks={str(ano): str(ano) for ano in df_suic['ano'].unique()},
                    step=None,
                    id='ano-suicidio'
                )
            ], width=12),
            dbc.Col([
                dcc.Graph(id='grafico-suicidios')
            ], width=12)
        ])

    elif aba == 'tab-sexo':
        return dbc.Row([
            dbc.Col([
                html.Label("Ano:"),
                dcc.Slider(
                    df_sexo['ano'].min(),
                    df_sexo['ano'].max(),
                    value=df_sexo['ano'].min(),
                    marks={str(ano): str(ano) for ano in df_sexo['ano'].unique()},
                    step=None,
                    id='ano-sexo'
                )
            ], width=12),
            dbc.Col([
                dcc.Graph(id='grafico-sexo')
            ], width=12)
        ])

@callback(
    Output('homicidios', 'figure'),
    Input('anos-homic', 'value')
)
def atualizar_mapa(ano):
    df_filtrado = df_uf[df_uf['ano'] == ano]

    fig = px.choropleth(
        df_filtrado,
        geojson=geojson_estados,
        locations='nome',
        featureidkey='properties.sigla',
        color='valor',
        color_continuous_scale='Reds',
        labels={'valor': 'Homicídios'},
        title=f"Homicídios por Estado - {ano}"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    return fig

@callback(
    Output('grafico-suicidios', 'figure'),
    Input('ano-suicidio', 'value')
)
def atualizar_suicidios(ano):
    df_filtrado = df_suic[df_suic['ano'] == ano].nlargest(5, 'valor')

    fig = px.bar(
        df_filtrado,
        x='nome',
        y='valor',
        labels={'nome': 'Estado', 'valor': 'Taxa de Suicídios'},
        title=f"Top 5 Estados - Suicídios por Armas de Fogo ({ano})"
    )
    fig.update_traces(text=df_filtrado['valor'].round(0), textposition='outside')
    fig.update_layout(yaxis_title="Taxa", xaxis_title="Estado", uniformtext_minsize=8, uniformtext_mode='hide')

    return fig

@callback(
    Output('grafico-sexo', 'figure'),
    Input('ano-sexo', 'value')
)
def atualizar_homicidios_sexo(ano):
    df_filtrado = df_sexo[df_sexo['ano'] == ano].groupby('sexo')['valor'].sum().reset_index()

    fig = px.pie(
        df_filtrado,
        names='sexo',
        values='valor',
        title=f"Homicídios por Sexo ({ano})",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)

