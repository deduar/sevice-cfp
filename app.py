
import os
from dotenv import load_dotenv

import threading
from flask import Flask

from service.service import SERVICE
from service.mongo import MONGO
from service.kafka_consumer import KAFKA_CONSUMER
from service.kafka_producer import KAFKA_PRODUCER
from service.mapping import MAPPING

from coco_cfp_pfm_es.cfp_pfm_es import config_bfm_es, config_bfm_es_v6, CFP

rest = Flask(__name__)

@rest.route('/')
def index():
    return 'Coinscrap'

@rest.route('/health')
def health():
    try:
        connect[connect.get_database()._Database__name].command('ping')
        return 'True'
    except Exception as e:
        # set response code to 500 and return with KO
        return 'False'

def main_rest():
    rest.run(port=3000, host='cfp-service')

def mongo_thread():
    main_rest(), threading.current_thread()

def main():

    print("LOAD ENV ---------")
    load_dotenv()
    print(os.environ.get('HTTP_PORT', '8080'))

    print("INIT MONGO  ---------")
    mong = MONGO()
    global connect
    connect = mong.client_connector()    

    print("STRAT APP main --------- FIRST ESTIMATE")
    SERVICE().run_service()

    print("STRAT FLASK   --------- START FLASK")
    t = threading.Thread(target=mongo_thread)
    t.start()
    
    print("STRAT APP main --------- SECOND ESTIMATE")
    SERVICE().run_service()

    print("MAPPING --------")
    mapp = MAPPING()
    df_map = mapp.load_mapping()

    print("INIT CFP CONFIG *****")
    cfp = CFP(conf=config_bfm_es.load())

    print("KAFKA CLIENT CONSUMER ----------")
    consumer = KAFKA_CONSUMER().consumer()

    print("KAFKA CLIENT PRODUCER ----------")
    producer = KAFKA_PRODUCER().producer()


    print("ESTIMATE EACH MESSAGE from consumer to producer ----------")
    for message in consumer:
        message = message.value
        df_cat_subCat = mapp.get_cat_subcat(mapp=df_map,cat_id=float(message['cat_id']))
        print("CAT SUBCAT ",df_cat_subCat)
        if len(df_cat_subCat) > 0 :
            mov_to_estimate = {
                "user_id": message["identifier"],
                "amount": message["amount"],
                "date": message["date"],
                "title": message["title"],
                "category":df_cat_subCat.iloc[0]['cat'],
                "subcategory": df_cat_subCat.iloc[0]['subcat']
            }
            print("ESTIMATE CFP .........")
            mov = cfp.dic_to_mov(dic=mov_to_estimate)
            estimate = cfp.estimateCFP(mov=mov)
            print(estimate)
            print("WRITE TO TOPIC PRODUCER -->")
            producer.send('t_cfp',value=estimate)
            print("UPSERT TO MONGO -->")

            count = {}
            for key, value in estimate.items():
                count[key] = 1 if value else 0

            increment = {"totalCO2":estimate["co2"],
                         "countCO2": count['co2'],
                         "totalN2O":estimate["n2o"],
                         "countN2O": count['n2o'],
                         "totalCH4":estimate["ch4"],
                         "countCH4": count['ch4'],
                         "totalH2O":estimate["h2o"],
                         "countH2O": count['h2o'],
                         "totalPlastic":estimate["sup"],
                         "countPlastic":count['sup']}

            #
            ## USER TRANSACTIONS
            db = connect[connect.get_database()._Database__name][os.environ.get('MONGO_COLLECTION', 'AgregatedCfp')]

            # Add transaction for user and date
            db.update_one({"identifier":mov_to_estimate["user_id"],"date":mov_to_estimate["date"]},
                        {"$set":{"aggregationPeriodicity":"daily"},
                        "$inc":increment},
                        True)
            # Agregation by User Global (startDate to null)
            db.update_one({"identifier":mov_to_estimate["user_id"],"date":None},
                        {"$set":{"aggregationPeriodicity":None},
                        "$inc":increment},
                        True)
        
            #
            ## GLOBAL TRANSACTONS
            # Global by date
            db.update_one({"identifier":None,"date":mov_to_estimate["date"]},
                        {"$set":{"aggregationPeriodicity":"daily"},
                        "$inc":increment},
                        True)
            # Global total
            db.update_one({"identifier":None,"date":None},
                        {"$set":{"startDate":None,"aggregationPeriodicity":None},
                        "$inc":increment},
                        True)

        else:
            print("MESSAGE NOT ESTIMATE", message)

if __name__ == "__main__":
    main()


