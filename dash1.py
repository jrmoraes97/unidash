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

# Carregando homicídios por raça/cor
df_negros = pd.read_csv("homicidios-negros.csv", sep=';', usecols=['nome', 'ano', 'valor'])
df_negros['grupo'] = 'Negros'

df_nao_negros = pd.read_csv("homicidios-nao-negros.csv", sep=';', usecols=['nome', 'ano', 'valor'])
df_nao_negros['grupo'] = 'Não Negros'

df_cor = pd.concat([df_negros, df_nao_negros], ignore_index=True)
df_cor['nome'] = df_cor['nome'].str.strip()

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

# Layout
app.layout = dbc.Container([
    html.H2("📊 Análise de Homicídios e Suicídios por Armas de Fogo", className="text-center my-4 text-primary"),

    dcc.Tabs(id="tabs", value='tab-mapa', children=[
        dcc.Tab(label='🗺️ Mapa de Homicídios', value='tab-mapa'),
        dcc.Tab(label='🔫 Top Estados Suicídios', value='tab-suicidios'),
        dcc.Tab(label='🎯 Homicídios por Cor/Raça', value='tab-cor')
    ]),

    html.Div(id='conteudo-abas')
], fluid=True)

# Alterna entre abas
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

    elif aba == 'tab-cor':
        return dbc.Row([
            dbc.Col([
                html.Label("Ano:"),
                dcc.Slider(
                    df_cor['ano'].min(),
                    df_cor['ano'].max(),
                    value=df_cor['ano'].min(),
                    marks={str(ano): str(ano) for ano in df_cor['ano'].unique()},
                    step=None,
                    id='ano-cor'
                )
            ], width=12),
            dbc.Col([
                dcc.Graph(id='grafico-cor')
            ], width=12)
        ])

# Mapa de calor de homicídios
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
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

    return fig

# Gráfico de suicídios
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

# Gráfico de homicídios por cor
@callback(
    Output('grafico-cor', 'figure'),
    Input('ano-cor', 'value')
)
def atualizar_homicidios_cor(ano):
    df_filtrado = df_cor[df_cor['ano'] == ano].groupby('grupo')['valor'].sum().reset_index()

    fig = px.pie(
        df_filtrado,
        names='grupo',
        values='valor',
        title=f"Homicídios por Cor/Raça ({ano})",
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)
