import os
from kafka import KafkaConsumer
from json import loads

class KAFKA_CONSUMER:

    def __init__(self) -> None:
        pass
        
    def consumer(self):
        return KafkaConsumer(
            "t_raw",
            bootstrap_servers=os.environ.get('KAFKA_SERVER', 'kafka')+':'+os.environ.get('KAFKA_PORT', '9093'),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=loads,
            # value_deserializer=lambda x: loads(x.decode('utf-8'))
        )
    