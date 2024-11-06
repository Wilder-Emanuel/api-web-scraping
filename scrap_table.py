import boto3
import requests
from bs4 import BeautifulSoup
import os
import uuid

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'TablaWebScrappingSismos')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web'
        }

    soup = BeautifulSoup(response.content, 'html.parser')

    # Buscar la tabla específica de sismos
    table = soup.find('table', {'class': 'table table-hover table-bordered table-light border-white w-100'})
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los datos de las filas de la tabla
    rows = []
    for row in table.find('tbody').find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 4:
            data = {
                'ReporteSismico': cells[0].text.strip(),
                'Referencia': cells[1].text.strip(),
                'FechaHora': cells[2].text.strip(),
                'Magnitud': cells[3].text.strip(),
                'id': str(uuid.uuid4())
            }
            rows.append(data)

    # Guardar los datos en DynamoDB
    with table.batch_writer() as batch:
        for item in rows:
            batch.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': 'Datos de sismos guardados correctamente en DynamoDB'
    }
