import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
import locale
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
import plotly.express as px
import plotly.graph_objects as go

def get_html(file):
    with open(file) as f:
        html = f.read()

    return BeautifulSoup(html, 'html.parser')

def extract_values(soup, divide=False):
    table_container = soup.find('div', {'class': 'table__scroll'})
    rows = table_container.findAll('tr')

    ## Saltarse la primera fila que son los headers
    results = []
    for row in rows[1:]:
        tds = row.findAll('td')

        tds = [td.text.strip() if td.text.strip() != 'n.d.' else None for td in tds]

        row_result = {
            'Mes': tds[0],
            'Precio m2': tds[1],
            'Variación mensual': tds[2],
            'Variación trimestral': tds[3],
            'Variación anual': tds[4]
        }
        
        results.append(row_result)

    df = pd.DataFrame(results)

    df['Fecha'] = pd.to_datetime(df['Mes'], format='%B %Y', errors='coerce')
    df = df.sort_values(by='Fecha', ascending=True)

    ## Quitar el €/m2 y el . de la columna Precio m2
    if divide:
        df['Precio m2'] = df['Precio m2'].replace({r'[^\d.,]': ''}, regex=True).replace('\.', '', regex=True).replace(',', '.', regex=True).astype(float) / 10
    else:
        df['Precio m2'] = df['Precio m2'].replace({r'[^\d.,]': ''}, regex=True).replace('\.', '', regex=True).replace(',', '.', regex=True).astype(float)

    ## Borrar las filas que no tengan datos de Precio m2
    df = df[~pd.isna(df['Precio m2'])]

    ## Quitar el % de las columnas de Variación y pasarlo a float
    df[['Variación mensual', 'Variación trimestral', 'Variación anual']] = \
        df[['Variación mensual', 'Variación trimestral', 'Variación anual']].apply(
            lambda x: x.replace('None', '0').replace('%', '', regex=True).replace('\s+', '', regex=True).replace(',', '.', regex=True).fillna(0).astype(float))

    ## Añadir 3 nuevas columnas con las variaciones
    df['Variación mensual €'] = df['Precio m2'] * (1 + df['Variación mensual'] / 100)
    df['Variación trimestral €'] = df['Precio m2'] * (1 + df['Variación trimestral'] / 100)
    df['Variación anual €'] = df['Precio m2'] * (1 + df['Variación anual'] / 100)

    return df

def plot_data(df, title):
    fig = go.Figure()

    fig.add_trace(
        go.Bar(x=df['Mes'],
            y=df['Precio m2'],
            name="Precio m2",
            marker=dict(color='royalblue'))
    )

    fig.add_trace(
        go.Scatter(x=df['Mes'],
                y=df['Variación mensual €'],
                mode='lines',
                name="Variación mensual",
                hovertemplate=(
                    'Mes: %{x}<br>'
                    'Variación mensual: %{y:.3f} €<br>' 
                    'Porcentaje: %{text}%<br>' 
                ),
                text=df['Variación mensual'].apply(lambda x: f"{x:.2f}"),
                line=dict(color='orange'))
    )

    fig.add_trace(
        go.Scatter(x=df['Mes'],
                y=df['Variación trimestral €'],
                mode='lines',
                name="Variación trimestral",
                hovertemplate=(
                    'Mes: %{x}<br>'
                    'Variación trimestral: %{y:.3f} €<br>' 
                    'Porcentaje: %{text}%<br>' 
                ),
                text=df['Variación trimestral'].apply(lambda x: f"{x:.2f}"),
                line=dict(color='forestgreen'))
    )

    fig.add_trace(
        go.Scatter(x=df['Mes'],
                y=df['Variación anual €'],
                mode='lines',
                name="Variación anual",
                hovertemplate=(
                    'Mes: %{x}<br>'
                    'Variación anual: %{y:.3f} €<br>' 
                    'Porcentaje: %{text}%<br>' 
                ),
                text=df['Variación anual'].apply(lambda x: f"{x:.2f}"),
                line=dict(color='indigo'))
    )

    fig.update_layout(
        title=title,
        xaxis_title="Mes",
        yaxis_title="Precio por m2",
        yaxis2=dict(
            title="Variación mensual (%)",
            overlaying='y',
            side='right'
        )
    )

    fig.show()