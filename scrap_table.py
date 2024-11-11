import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    # URL de la página web que contiene la tabla de sismos
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    # Realizar la solicitud HTTP a la página web
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web'
        }

    # Parsear el contenido HTML de la página web
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrar la tabla en el HTML
    table = soup.find('table')
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los encabezados de la tabla
    headers = [header.text for header in table.find_all('th')]

    # Extraer las 10 primeras filas de la tabla
    rows = []
    for row in table.find_all('tr')[1:11]:  # Extraer solo las primeras 10 filas después del encabezado
        cells = row.find_all('td')
        rows.append({headers[i]: cell.text for i, cell in enumerate(cells)})

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('SismosReportados')

    # Insertar los datos en la tabla DynamoDB
    for row in rows:
        row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
        table.put_item(Item=row)

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': rows
    }
