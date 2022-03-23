import json

from flask import Flask, session
from dynamodb_session_flask import DynamoDbSession

LOCAL_ENDPOINT = 'http://localhost:8000'
TABLE_NAME = 'app_session'


def recreate_database():
    import boto3
    import botocore
    dynamodb = boto3.resource('dynamodb', endpoint_url=LOCAL_ENDPOINT)

    try:
        # Create the DynamoDB table.
        return dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }],
            AttributeDefinitions=[{
                'AttributeName': 'id',
                'AttributeType': 'S'
            }],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
    except botocore.exceptions.ClientError:
        pass


def print_table_data(table):
    from decimal import Decimal

    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return str(obj)
            return json.JSONEncoder.default(self, obj)

    response = table.scan(
        Select='ALL_ATTRIBUTES',
        ConsistentRead=True
    )
    if len(response.get('Items', [])) > 0:
        print(json.dumps(response['Items'], indent=2, cls=DecimalEncoder))
    else:
        print('>>>> No Data in DynamoDB <<<<')


dynamo_table = recreate_database()


def default_example():
    flask_app = Flask(__name__)
    flask_app.config.update({
        'TESTING': True,
        'SESSION_DYNAMODB_ENDPOINT_URL': 'http://localhost:8000',
        'SESSION_DYNAMODB_USE_HEADER': True
    })
    flask_app.session_interface = DynamoDbSession()

    @flask_app.route('/save/<val>')
    def save(val):
        session['val'] = val
        return '', 200

    @flask_app.route('/load')
    def load():
        return {
            'saved_val': session.get('val', None),
        }

    return flask_app


default_example().run()
