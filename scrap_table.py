from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import boto3
import uuid
import time

def lambda_handler(event, context):
    # Configurar Selenium para AWS Lambda
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Crear instancia de Chrome para Selenium
    service = Service('/path/to/chromedriver') # Especifica la ruta de chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # URL de la página web que contiene la tabla
    url = "https://ultimosismo.igp.gob.pe/ultimosismo/sismos-reportados"

    # Abrir la página web
    driver.get(url)

    # Esperar unos segundos para que se cargue el contenido dinámico
    time.sleep(5)

    # Obtener el HTML renderizado
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit() # Cerrar el navegador

    # Encontrar la tabla en el HTML
    table = soup.find('table')
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los encabezados de la tabla
    headers = [header.text.strip() for header in table.find_all('th')]

    # Extraer las filas de la tabla
    rows = []
    for row in table.find_all('tr')[1:]: # Omitir el encabezado
        cells = row.find_all('td')
        rows.append({headers[i]: cells[i].text.strip() for i in range(len(cells))})

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrappingSismos')

    # Eliminar todos los elementos de la tabla antes de agregar los nuevos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key={'id': each['id']})

    # Insertar los nuevos datos
    i = 1
    for row in rows:
        row['#'] = i
        row['id'] = str(uuid.uuid4()) # Generar un ID único para cada entrada
        table.put_item(Item=row)
        i += 1

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': rows
    }
