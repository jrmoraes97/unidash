from dash import Dash, html, dcc, Output, Input, callback
import plotly.express as px
import pandas as pd
import json
import requests


app = Dash(__name__)

# Carregando dados de homicídios
df_uf = pd.read_csv("homic-estados.csv", sep=';', usecols=['nome','ano', 'valor'])
df_uf['nome'] = df_uf['nome'].str.strip()

# Carregando dados de suicidios
df_suic = pd.read_csv("taxa-suicidios-por-armas-de-fogo.csv", sep=';', usecols=['nome','ano', 'valor'])
df_suic['nome'] = df_suic['nome'].str.strip()

# Carregando homicídios por sexo (com estados)
df_homens = pd.read_csv("homic-homens.csv", sep=';', usecols=['nome', 'ano', 'valor'])
df_homens['sexo'] = 'Homens'

df_mulheres = pd.read_csv("homic-mulheres.csv", sep=';', usecols=['nome', 'ano', 'valor'])
df_mulheres['sexo'] = 'Mulheres'

# Unificando os dados
df_sexo = pd.concat([df_homens, df_mulheres], ignore_index=True)
df_sexo['nome'] = df_sexo['nome'].str.strip()  


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
    nome = feature['properties']['name']
    feature['properties']['sigla'] = siglas.get(nome)

app.layout = html.Div([
    html.H2("Análise de Homicídios no Brasil", style={
        "textAlign": "center",
        "marginTop": "20px"
    }),

    html.Div([
        dcc.Slider(
            df_uf['ano'].min(),
            df_uf['ano'].max(),
            value=df_uf['ano'].min(),
            marks={str(ano): str(ano) for ano in df_uf['ano'].unique()},
            step=None,
            id='anos-homic'
        )
    ], style={"width": "80%", "margin": "auto", "paddingBottom": "30px"}),

    # Mapa centralizado
    html.Div([
        dcc.Graph(id='homicidios')
    ], style={"width": "80%", "margin": "auto", "paddingBottom": "30px"}),

    html.Div(className="divisor"),

    # Linha com os dois gráficos lado a lado
    html.Div([
    html.Div([
        dcc.Graph(id='grafico-suicidios')
    ], style={
        "width": "50%", 
        "padding": "10px", 
        "boxSizing": "border-box"
    }),

    html.Div([
        dcc.Graph(id='comparativo-sexo')
    ], style={
        "width": "50%", 
        "padding": "10px", 
        "boxSizing": "border-box"
    })
    ], style={
        "display": "flex",
        "flexDirection": "row",
        "justifyContent": "center",
        "alignItems": "stretch",
        "width": "100%",
        "margin": "auto"
    })
])


@callback(
    Output('homicidios', 'figure'),
    Output('grafico-suicidios', 'figure'),
    Output('comparativo-sexo', 'figure'),
    Input('anos-homic', 'value')
)

def atualizar_mapa(selected_ano):
    filtered_df = df_uf[df_uf['ano'] == selected_ano]

    fig = px.choropleth(
        filtered_df,
        geojson=geojson_estados,
        locations='nome',
        featureidkey='properties.sigla',
        color='valor',
        color_continuous_scale='Reds',
        labels={'valor': 'Homícidos'},
        title=f"Homicídios por Estado - {selected_ano}"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    df_s_ano = df_suic[df_suic['ano'] == selected_ano]
    df_top5 = df_s_ano.nlargest(5, 'valor').sort_values('valor', ascending=True)  # Para barra horizontal
    fig_suic = px.bar(
        df_top5,
        x='valor',
        y='nome',
        orientation='h',
        title=f"Top Estados - Suicídios por Armas de Fogo ({selected_ano})",
        labels={'valor': 'Suicídios', 'nome': 'Estado'}
    )
    


    df_sexo_ano = df_sexo[df_sexo['ano'] == selected_ano]
    df_total_sexo = df_sexo_ano.groupby('sexo', as_index=False)['valor'].sum()

    fig_sexo = px.bar(
        df_total_sexo,
        x='sexo',
        y='valor',
        color='sexo',
        title=f"Homicídios de Homens/Mulheres no Brasil ({selected_ano})",
        labels={'valor': 'Homicídios', 'sexo': 'Sexo'},
        text='valor'
    )
    fig_sexo.update_traces(textposition='outside')

    return fig, fig_suic, fig_sexo



if __name__ == '__main__':
    app.run(debug=True)
