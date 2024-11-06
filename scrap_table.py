import boto3
import os
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'TablaWebScrappingSismosDev')
table = dynamodb.Table(table_name)

# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Ruta al driver de Chrome
chrome_driver_path = '/path/to/chromedriver'

def scrape_and_store():
    # Inicializar Selenium WebDriver
    driver = webdriver.Chrome(chrome_driver_path, options=options)
    driver.get("https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados")

    # Esperar a que la página cargue completamente
    driver.implicitly_wait(10)  # espera de 10 segundos

    # Obtener el HTML de la página
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Encontrar la tabla dentro del componente <app-table>
    table = soup.find('app-table')
    if not table:
        driver.quit()
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    rows = []
    for row in table.find_all('tr')[1:]:  # Ignorar la fila de encabezado
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

    driver.quit()

    return {
        'statusCode': 200,
        'body': 'Datos de sismos guardados correctamente en DynamoDB'
    }

# Llamar a la función principal si es necesario
if __name__ == "__main__":
    scrape_and_store()
