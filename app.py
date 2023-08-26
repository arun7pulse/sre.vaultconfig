#!/usr/bin/python3
import argparse
import sys
import time
import json
import logging
from flask import Flask, Response
import os
import base64
import yaml
from logging.handlers import TimedRotatingFileHandler

article_info = [
    {
        'Details': {
            'domain': 'www.vaultconfig.com',
            'language': 'python',
            'date': '01/04/2023'
        }
    }
]

with open("configfile.yml", 'w') as yamlfile:
    data = yaml.dump(article_info, yamlfile)
    print("Write successful")

app = Flask(__name__)

configfile = f"configfile.yml"


def load_config():
    with open(configfile) as data:
        configdict = yaml.safe_load(data)
    return configdict


@app.route("/config", methods=['GET'])
def get_config():
    jsonstring = json.dumps(load_config(), ensure_ascii=False)
    # , charset='utf-8')
    response = Response(jsonstring, content_type='application/json')
    return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This is a demo.')
    parser.add_argument("-l", "--log", dest="logLevel", choices=[
                        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help="Set the logging level")

    args = parser.parse_args()
    filename = os.path.basename(__file__).rsplit('.', 1)[0]
    # logging.basicConfig(filename = f"{filename}.log", level = logging.INFO, format = '%(asctime)s:%(levelname)s:%(message)s')

    LOGFILE = ''
    logger = logging.getLogger(__name__)
    format = '%(asctime)s-[%(levelname)s]-[%(name)s]::%(message)s'
    # fileHandler = logging.FileHandler(f"{os.path.abspath(__file__)}.log")
    fileHandler = TimedRotatingFileHandler(
        f"{__name__}.log", when='d', interval=1, backupCount=30)
    streamHandler = logging.StreamHandler()
    fileHandler.setFormatter(logging.Formatter(format))
    streamHandler.setFormatter(logging.Formatter(format))
    logging.basicConfig(
        # format='%(asctime)s-[%(levelname)s]-[%(name)s]::%(message)s',
        level=getattr(logging, args.logLevel),
        handlers=[fileHandler, streamHandler]
        #  datefmt='%Y-%m-%d %H:%M:%S',
        # filename = f"{filename}.log",
    )
    logger.info(f"Log enabled in Main::::{args.logLevel}.")
    app.run(host='127.0.0.1', port=int('5000'), debug=True)
