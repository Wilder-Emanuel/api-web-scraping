from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import boto3
import uuid
import time

def lambda_handler(event, context):
    # Configurar Selenium con el controlador de Chrome
    options = webdriver.ChromeOptions()
    options.headless = True  # Ejecuta Chrome en modo sin interfaz gráfica
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # URL de la página web de sismos
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
    driver.get(url)

    # Esperar a que la tabla se cargue
    time.sleep(5)  # Ajusta el tiempo según sea necesario

    try:
        # Buscar la tabla en el HTML
        table = driver.find_element(By.TAG_NAME, 'table')
        headers = [header.text for header in table.find_elements(By.TAG_NAME, 'th')]
        
        # Extraer los datos de las filas de la tabla
        rows = []
        for row in table.find_elements(By.TAG_NAME, 'tr')[1:11]:  # Solo las primeras 10 filas
            cells = row.find_elements(By.TAG_NAME, 'td')
            rows.append({headers[i]: cells[i].text for i in range(len(cells))})

        # Guardar los datos en DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('SismosReportados')
        for row in rows:
            row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
            table.put_item(Item=row)

        # Retornar el resultado como JSON
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
