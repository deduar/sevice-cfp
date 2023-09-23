import os
from kafka import KafkaProducer
from json import dumps

class KAFKA_PRODUCER:

    def __init__(self) -> None:
        pass
        
    def producer(self):
        return KafkaProducer(
            bootstrap_servers=os.environ.get('KAFKA_SERVER', 'kafka')+':'+os.environ.get('KAFKA_PORT', '9093'),
            value_serializer=lambda x: dumps(x).encode('utf-8',),
            # sasl_plain_username=EnvVariables.SASL_PLAIN_USERNAME.get_env(),
            # sasl_plain_password=EnvVariables.SASL_PLAIN_PASSWORD.get_env()
        )
