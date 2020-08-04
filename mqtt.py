import re
import requests
import time
import json
import paho.mqtt.client as mqtt
import argparse

def parseCookieFile(cookiefile):
    cookies = {}
    with open (cookiefile, 'r') as fp:
        for line in fp:
            if not re.match(r'^\#', line):
                lineFields = line.strip().split('\t')
                cookies[lineFields[5]] = lineFields[6]
    return cookies


## Parse arguments into variables
parser = argparse.ArgumentParser()
parser.add_argument("cookie_path")
parser.add_argument("mqtt_server")
parser.add_argument("mqtt_user")
parser.add_argument("mqtt_password")
parser.add_argument("mqtt_port")

args = parser.parse_args()
cookie_path = args.cookie_path
mqtt_server = args.mqtt_server
mqtt_user = args.mqtt_user
mqtt_password = args.mqtt_password
mqtt_port  =int(args.mqtt_port)

## Parse cookiefile
cookies = parseCookieFile(cookie_path+'/cookies.txt')

## Get field_id from cookie file
for cookiename in cookies:
    if cookiename == 'SolarEdge_Field_ID':
        field_id = cookies[cookiename]

## Connect to MQTT server
client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_password)
client.connect(mqtt_server, mqtt_port, 60)

while 1:
    try:
        r = requests.get('https://monitoring.solaredge.com/solaredge-apigw/api/sites/'+field_id+'/layout/logical', cookies=cookies)
        datajson = json.loads(r.content)
        for data in datajson['reportersInfo']:
            if datajson['reportersInfo'][data]['lastMeasurement'] != None:
                client.publish("solaredge/"+str(datajson['reportersInfo'][data]['name'])+"/unscaledEnergy",str(datajson['reportersData'][data]['unscaledEnergy']))
                client.publish("solaredge/"+str(datajson['reportersInfo'][data]['name'])+'/lastMeasurement',int(datajson['reportersInfo'][data]['lastMeasurement']/1000))
                for measurements in datajson['reportersInfo'][data]:
                    if measurements in ('localizedMeasurements', 'localizedPhase1Measurements', 'localizedPhase2Measurements', 'localizedPhase3Measurements'):
                        for value in datajson['reportersInfo'][data][measurements]:
                            client.publish("solaredge/"+str(datajson['reportersInfo'][data]['name'])+'/'+measurements+'/'+value,str(datajson['reportersInfo'][data][measurements][value]).replace('.',''))
    except:
        print("[Error] Unknown error")
    time.sleep(60)



