import boto3
import requests
from bs4 import BeautifulSoup
import os
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

    # Buscar la tabla específica en el HTML utilizando sus clases
    table = soup.find('table', {'class': 'table-bordered table-light'})
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los datos de las filas de la tabla
    rows = []
    for row in table.find('tbody').find_all('tr'):  # Buscar en el <tbody>
        cells = row.find_all('td')
        if len(cells) >= 4:  # Asegurarse de que hay suficientes columnas
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
    table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'TablaWebScrappingSismosDev'))

    # Insertar los nuevos datos
    with table.batch_writer() as batch:
        for row in rows:
            batch.put_item(Item=row)

    return {
        'statusCode': 200,
        'body': 'Datos de sismos guardados correctamente en DynamoDB'
    }

# Llamar a la función principal si es necesario
if __name__ == "__main__":
    lambda_handler(None, None)
