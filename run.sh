#!/usr/bin/with-contenv bashio

CONFIG_PATH=/data/options.json
cookie_path=$(jq --raw-output ".cookie_path" $CONFIG_PATH)
mqtt_server=$(jq --raw-output ".mqtt_server" $CONFIG_PATH)
mqtt_user=$(jq --raw-output ".mqtt_user" $CONFIG_PATH)
mqtt_password=$(jq --raw-output ".mqtt_password" $CONFIG_PATH)
mqtt_port=$(jq --raw-output ".mqtt_port" $CONFIG_PATH)

mkdir -p $cookie_path
echo "[Info] Cookie path is ".$cookie_path

if [[ ! -f $cookie_path/cookies.txt ]]; then
    echo "[Error] No cookies.txt file found in cookie path. Place cookies.txt in the cookie path and restart the add-on."
fi

python3 ./mqtt.py $cookie_path $mqtt_server $mqtt_user $mqtt_password $mqtt_port