import boto3
import os
import uuid
from bs4 import BeautifulSoup

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'TablaWebScrappingSismosDev')
table = dynamodb.Table(table_name)

def scrape_and_store():
    # Leer el contenido del archivo HTML
    with open("htmlSismos.txt", "r", encoding="utf-8") as file:
        html_content = file.read()

    # Parsear el contenido HTML del archivo
    soup = BeautifulSoup(html_content, 'html.parser')

    # Buscar la tabla específica en el HTML utilizando sus clases
    table = soup.find('table', {'class': 'table-bordered table-light'})
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en el HTML proporcionado'
        }

    # Extraer los datos de las filas de la tabla
    rows = []
    for row in table.find('tbody').find_all('tr'):
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
    with table.batch_writer() as batch:
        for item in rows:
            batch.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': 'Datos de sismos guardados correctamente en DynamoDB'
    }

# Llamar a la función principal si es necesario
if __name__ == "__main__":
    scrape_and_store()
