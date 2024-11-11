import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import boto3
import uuid
import time

def lambda_handler(event, context):
    # Agregar el directorio /opt/bin al PATH para encontrar chromedriver
    os.environ["PATH"] += os.pathsep + "/opt/bin"

    # Configuración de opciones de Selenium
    options = webdriver.ChromeOptions()
    options.binary_location = "/opt/bin/headless-chromium"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Iniciar el controlador Chrome
    driver = webdriver.Chrome(
        executable_path="/opt/bin/chromedriver",
        options=options
    )

    # URL de la página de sismos
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
    driver.get(url)
    time.sleep(5)  # Espera para permitir la carga de contenido dinámico

    # Extraer los datos de la tabla de sismos
    try:
        table = driver.find_element(By.TAG_NAME, 'table')
        headers = [header.text for header in table.find_elements(By.TAG_NAME, 'th')]
        rows = []

        # Extraer las primeras 10 filas de la tabla
        for row in table.find_elements(By.TAG_NAME, 'tr')[1:11]:
            cells = row.find_elements(By.TAG_NAME, 'td')
            rows.append({headers[i]: cells[i].text for i in range(len(cells))})

        # Guardar los datos en DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('SismosReportados')
        for row in rows:
            row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
            table.put_item(Item=row)

        response = {
            'statusCode': 200,
            'body': rows
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': f"Error al procesar la página: {str(e)}"
        }
    finally:
        driver.quit()

    return response
