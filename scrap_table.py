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

    # Definir los encabezados de la tabla para los datos relevantes
    headers = ['Reporte Sísmico', 'Referencia', 'Fecha y Hora', 'Magnitud']

    # Extraer las filas de la tabla
    rows = []
    for row in table.find_all('tr')[1:]:  # Omitir el encabezado
        cells = row.find_all('td')
        if len(cells) >= 4:  # Asegurar que hay suficientes columnas
            data = {
                'ReporteSismico': cells[0].text.strip(),
                'Referencia': cells[1].text.strip(),
                'FechaHora': cells[2].text.strip(),
                'Magnitud': cells[3].text.strip(),
                'id': str(uuid.uuid4())  # Generar un ID único para cada entrada
            }
            rows.append(data)

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping')

    # Eliminar todos los elementos de la tabla antes de agregar los nuevos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key={'id': each['id']})

    # Insertar los nuevos datos
    for row in rows:
        table.put_item(Item=row)

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': rows
    }
