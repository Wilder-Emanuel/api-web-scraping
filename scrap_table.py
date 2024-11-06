import boto3
import os
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'TablaWebScrappingSismos')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Configuración de Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Ruta al driver de Chrome
    driver_path = '/path/to/chromedriver'  # Reemplaza con la ruta a tu ChromeDriver

    # Inicializar el navegador con Selenium
    driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    driver.get("https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados")

    # Esperar a que la página cargue completamente
    driver.implicitly_wait(10)

    # Obtener el HTML de la página cargada con JavaScript
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    driver.quit()

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
