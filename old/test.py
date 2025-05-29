import json
import threading
import configparser
from uuid import uuid4

import boto3
from awscrt import auth, io, mqtt
from awsiot import mqtt_connection_builder, iotshadow


config = configparser.ConfigParser()
config.read("aws.ini")

account_id = config['auth']['account_id']
cafile     = config['auth']['cafile']

endpoint = config['iot']['endpoint']
region   = config['iot']['region']
topic    = config['iot']['topic']
things   = config['iot']['things']
shadow_name = "shadow"

# =====================
# 動的権限取得
# =====================

policy = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {"Action": ["iot:Connect", "iot:Publish", "iot:Receive", "iot:Subscribe"], "Effect": "Allow", "Resource": "*"},
        ],
    }
)

client = boto3.client('sts')
response = client.assume_role(
    RoleArn=f'arn:aws:iam::{account_id}:role/sts-sample-role',
    RoleSessionName="test-" + str(uuid4()),
    Policy=policy,
)

credentials = response['Credentials']

# =====================
# MQTT接続処理
# =====================
credentials_provider = auth.AwsCredentialsProvider.new_static(
    access_key_id=credentials['AccessKeyId'],
    secret_access_key=credentials['SecretAccessKey'],
    session_token=credentials['SessionToken'],
)


event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
    client_id="id-" + str(uuid4()),
    endpoint=endpoint,
    client_bootstrap=client_bootstrap,
    cafile=cafile,
    region=region,
    clean_session=False,
    websocket_proxy_options=None,
    credentials_provider=credentials_provider,
    keep_alive_secs=6,
)


connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected!")

shadow = iotshadow.IotShadowClient(mqtt_connection)

received_all_event = threading.Event()


def on_update_shadow_accepted(response: iotshadow.UpdateShadowResponse):
    print("Shadow Update Accepted:")
    print(response.state)


def on_get_shadow_accepted(response: iotshadow.GetShadowResponse):
    print("Shadow Get Accepted:")
    print(response.state)


shadow.subscribe_to_update_shadow_accepted(
    iotshadow.ShadowUpdatedSubscriptionRequest(thing_name=things),
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_update_shadow_accepted,
)

shadow.subscribe_to_get_shadow_accepted(
    iotshadow.GetShadowSubscriptionRequest(thing_name=things),
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_get_shadow_accepted,
)

client = boto3.client("iot-data")
response = client.get_thing_shadow(thingName=things)
# StreamingBodyからデータを読み込む
stream = response["payload"]
shadow_payload = stream.read()
# バイトデータをJSONにデコード
shadow_data = json.loads(shadow_payload)
# デコードされたデータを表示
print(shadow_data)


#get_shadow_future = shadow.publish_get_shadow(
#    request=iotshadow.GetShadowRequest(thing_name=things),
#    qos=mqtt.QoS.AT_LEAST_ONCE,
#)
#get_shadow_future.result()

## test publish
data = {"state":{"desired":{"direction":True}}}
mqtt_connection.publish(topic="$aws/things/01238F3A6EEFE30201/shadow/update", payload=json.dumps(data), qos=mqtt.QoS.AT_LEAST_ONCE)
print("Published: '" + json.dumps(data) + "' to the topic: " + topic)

received_all_event.wait()

## test subscribe
# def on_message_received(topic, payload, dup, qos, retain, **kwargs):
#     print("Received message from topic '{}': {}".format(topic, payload))
# 
# print("Subscribing to topic '{}'...".format(topic))
# subscribe_future, packet_id = mqtt_connection.subscribe(
#     topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_message_received
# )

# subscribe_result = subscribe_future.result()
# print("Subscribed with {}".format(str(subscribe_result['qos'])))