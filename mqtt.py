import re
import requests
import time
import json
import paho.mqtt.client as mqtt
import argparse
import sys

def parseCookieFile(cookiefile):
    cookies = {}
    with open (cookiefile, 'r') as fp:
        for line in fp:
            if not re.match(r'^\#', line):
                lineFields = line.strip().split('\t')
                cookies[lineFields[5]] = lineFields[6]
    return cookies

def clean_name(name):
    name = name.replace(' ','_').replace('.','-')
    return name

def publish_config_inverter(name,dimension,unit_of_measurement, datajson):
    values = {}
    values['name'] = name+'_'+dimension
    values['unique_id'] = name+'_'+dimension
    if dimension == 'power':
        values['device_class'] = dimension
    values['state_topic'] = 'homeassistant/sensor/'+name
    values['json_attributes_topic'] = 'homeassistant/sensor/'+name
    values['value_template']= '{{ value_json.'+dimension+' }}'
    if (unit_of_measurement != None):
        values['unit_of_measurement'] = unit_of_measurement
    values['device'] = {}
    values['device']['name'] = name
    values['device']['manufacturer'] = datajson['manufacturer']
    values['device']['model'] = datajson['model']
    values['device']['identifiers'] = ('solaredge_'+ name,)
    json_data = json.dumps(values)
    client.publish(config_base_topic+'/'+dimension+'/config',json_data,retain=True)

def publish_config_panel(name,dimension,unit_of_measurement, datajson):
    values = {}
    values['name'] = name+'_'+dimension
    values['unique_id'] = name+'_'+dimension
    if dimension == 'power':
        values['device_class'] = dimension
    values['state_topic'] = 'homeassistant/sensor/'+name
    values['json_attributes_topic'] = 'homeassistant/sensor/'+name
    values['value_template']= '{{ value_json.'+dimension+' }}'
    if (unit_of_measurement != None):
        values['unit_of_measurement'] = unit_of_measurement
    values['device'] = {}
    values['device']['name'] = name
    values['device']['manufacturer'] = datajson['manufacturer']
    values['device']['model'] = datajson['model']
    values['device']['identifiers'] = ('solaredge_'+ name,)
    json_data = json.dumps(values)
    client.publish(config_base_topic+'/'+dimension+'/config',json_data,retain=True)

def publish_values_inverter(name):
    dimensions_l1 = ('l1_active_power', 'l1_current', 'l1_voltage')
    dimensions_l2 = ('l2_active_power', 'l2_current', 'l2_voltage')
    dimensions_l3 = ('l3_active_power', 'l3_current', 'l3_voltage')
    translations_l1 = {}
    translations_l1['l1_active_power'] = 'Actief vermogen [W]'
    translations_l1['l1_current'] = 'I AC [A]'
    translations_l1['l1_voltage'] = 'V AC [V]'
    translations_l2 = {}
    translations_l2['l2_active_power'] = 'Actief vermogen [W]'
    translations_l2['l2_current'] = 'I AC [A]'
    translations_l2['l2_voltage'] = 'V AC [V]'
    translations_l3 = {}
    translations_l3['l3_active_power'] = 'Actief vermogen [W]'
    translations_l3['l3_current'] = 'I AC [A]'
    translations_l3['l3_voltage'] = 'V AC [V]'
    values = {}
    if len(systemData['phase1Measurements'])>0:
        for dimension in dimensions_l1:
            dimension_local = translations_l1[dimension]
            values[dimension] = systemData['phase1Measurements'][dimension_local].replace('.', '').replace(',','.')
            values[dimension] = float(values[dimension])
    if len(systemData['phase2Measurements'])>0:
        for dimension in dimensions_l2:
            dimension_local = translations_l2[dimension]
            values[dimension] = systemData['phase2Measurements'][dimension_local].replace('.', '').replace(',','.')
            values[dimension] = float(values[dimension])
    if len(systemData['phase3Measurements'])>0:
        for dimension in dimensions_l3:
            dimension_local = translations_l3[dimension]
            values[dimension] = systemData['phase3Measurements'][dimension_local].replace('.', '').replace(',','.')
            values[dimension] = float(values[dimension])
    json_data = json.dumps(values)
    client.publish('homeassistant/sensor/'+name,json_data)

def publish_values_panel(name):
    dimensions = ('power', 'current', 'voltage', 'optimizer_voltage')
    translations = {}
    translations['power'] = 'Vermogen [W]'
    translations['current'] = 'Stroom [A]'
    translations['voltage'] = 'Spanning [V]'
    translations['optimizer_voltage'] = 'Optimizer spanning [V]'
    values = {}
    for dimension in dimensions:
        dimension_local = translations[dimension]
        values[dimension] = systemData['measurements'][dimension_local].replace(',','.')
        values[dimension] = float(values[dimension])
    json_data = json.dumps(values)
    client.publish('homeassistant/sensor/'+name,json_data)


## Parse arguments into variables
parser = argparse.ArgumentParser()
parser.add_argument("cookie_path")
parser.add_argument("mqtt_server")
parser.add_argument("mqtt_user")
parser.add_argument("mqtt_password")
parser.add_argument("mqtt_anonymous")
parser.add_argument("mqtt_port")

args = parser.parse_args()
cookie_path = args.cookie_path
mqtt_server = args.mqtt_server
mqtt_user = args.mqtt_user
mqtt_password = args.mqtt_password
mqtt_anomymous = args.mqtt_anonymous
mqtt_port  =int(args.mqtt_port)

## Parse cookiefile
cookies = parseCookieFile(cookie_path+'/cookies.txt')

## Get field_id from cookie file
for cookiename in cookies:
    if cookiename == 'SolarEdge_Field_ID':
        field_id = cookies[cookiename]

while 1:
    try:
        ## Connect to MQTT server
        client = mqtt.Client()
        if mqtt_anomymous != True:
            client.username_pw_set(mqtt_user, mqtt_password)
        client.connect(mqtt_server, mqtt_port, 60)

        r = requests.get('https://monitoring.solaredge.com/solaredge-apigw/api/sites/'+field_id+'/layout/logical', cookies=cookies)
        datajson = json.loads(r.content)
        for data in datajson['logicalTree']['children']:
            # Omvormer
            panelId = data['data']['id']
            serialNumber = data['data']['serialNumber']
            name = data['data']['name']
            producttype = data['data']['type']                    
            r = requests.get('https://monitoring.solaredge.com/solaredge-web/p/systemData?reporterId='+str(panelId)+'&type='+producttype+'&activeTab=0&fieldId='+str(field_id)+'&isPublic=false', cookies=cookies)
            regexed = re.findall(r'SE\.systemData = .*',r.text)
            systemData = regexed[0][16:-1]
            systemData = json.loads(systemData)
            if systemData != None:
                name = str(systemData['description'])
                config_base_topic = 'homeassistant/sensor/'+name
                config_base_topic = config_base_topic.replace(' ','_').replace('.','-')
                name = clean_name(name)
                if (producttype == "INVERTER" or producttype == "INVERTER_3PHASE"):
                    # L1
                    if len(systemData['phase1Measurements'])>0:
                        publish_config_inverter(name, 'l1_active_power', 'W', systemData)
                        publish_config_inverter(name, 'l1_voltage', 'V', systemData)
                        publish_config_inverter(name, 'l1_current', 'A', systemData)
                    # L2
                    if len(systemData['phase2Measurements'])>0:
                        publish_config_inverter(name, 'l2_active_power', 'W', systemData)
                        publish_config_inverter(name, 'l2_voltage', 'V', systemData)
                        publish_config_inverter(name, 'l2_current', 'A', systemData)
                    # L3
                    if len(systemData['phase3Measurements'])>0:
                        publish_config_inverter(name, 'l3_active_power', 'W', systemData)
                        publish_config_inverter(name, 'l3_voltage', 'V', systemData)
                        publish_config_inverter(name, 'l3_current', 'A', systemData)
                    publish_values_inverter(name)
            
            # Panels
            for string in datajson['logicalTree']['children'][0]['children']:
                for panel in string['children']:
                    panelId = panel['data']['id']
                    serialNumber = panel['data']['serialNumber']
                    name = panel['data']['name']
                    displayName = panel['data']['displayName']
                    producttype = panel['data']['type']                    
                    r = requests.get('https://monitoring.solaredge.com/solaredge-web/p/systemData?reporterId='+str(panelId)+'&type='+producttype+'&activeTab=0&fieldId='+str(field_id)+'&isPublic=false', cookies=cookies)
                    regexed = re.findall(r'SE\.systemData = .*',r.text)
                    systemData = regexed[0][16:-1]
                    systemData = json.loads(systemData)

                    if systemData != None:

                        name = str(systemData['description'])
                        config_base_topic = 'homeassistant/sensor/'+name
                        config_base_topic = config_base_topic.replace(' ','_').replace('.','-')
                        
                        name = clean_name(name)
                        if (producttype=="POWER_BOX"):
                            publish_config_panel(name, 'power', 'W', systemData)
                            publish_config_panel(name, 'current', 'A', systemData)
                            publish_config_panel(name, 'voltage', 'V', systemData)
                            publish_config_panel(name, 'optimizer_voltage', 'V', systemData)
                            publish_values_panel(name)

        time.sleep(1)
        client.disconnect()
    except:
        e = sys.exc_info()[0]
        print("[Error] %s" % e)
    time.sleep(60)



