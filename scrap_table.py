import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    # URL de la página web que contiene la tabla
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    # Realizar la solicitud HTTP a la página web
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web'
        }

    # Parsear el contenido HTML de la respuesta
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrar la tabla en el HTML (ajusta los parámetros de búsqueda según la estructura del HTML)
    table = soup.find('table', {'class': 'table table-hover table-bordered table-light border-white w-100'})
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los encabezados de la tabla
    headers = [header.text.strip() for header in table.find('thead').find_all('th')]

    # Extraer las filas de la tabla
    rows = []
    for row in table.find('tbody').find_all('tr'):
        cells = row.find_all('td')
        row_data = {headers[i]: cells[i].text.strip() for i in range(len(cells))}
        rows.append(row_data)

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping')

    # Eliminar todos los elementos de la tabla antes de agregar los nuevos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    # Insertar los nuevos datos
    for i, row in enumerate(rows, start=1):
        row['#'] = i
        row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
        table.put_item(Item=row)

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': rows
    }
