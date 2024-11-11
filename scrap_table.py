import requests
import boto3
import uuid

def lambda_handler(event, context):
    # URL de la API de sismos
    url = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/2024"

    # Realizar la solicitud HTTP a la API
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la API de sismos'
        }

    # Parsear los datos JSON de la API
    data = response.json()

    # Extraer los primeros 10 registros
    sismos = data[:10]

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('SismosReportados')

    for sismo in sismos:
        # Añadir un ID único a cada registro
        sismo['id'] = str(uuid.uuid4())
        table.put_item(Item=sismo)

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': sismos
    }
