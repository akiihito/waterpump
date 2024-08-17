import json
import threading
import configparser
from uuid import uuid4

import boto3
from awscrt import auth, io, mqtt
from awsiot import mqtt_connection_builder


config = configparser.ConfigParser()
config.read("aws.ini")

account_id = config['auth']['account_id']
cafile     = config['auth']['cafile']

endpoint = config['iot']['endpoint']
region   = config['iot']['region']
topic    = config['iot']['topic']

# =====================
# 動的権限取得
# =====================
policy = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {"Action": "iot:Connect", "Effect": "Allow", "Resource": "*"},
            {
                "Action": ["iot:Publish", "iot:Receive"],
                "Effect": "Allow",
                "Resource": f"arn:aws:iot:*:*:topic/{topic}",
            },
            {
                "Action": ["iot:Subscribe"],
                "Effect": "Allow",
                "Resource": f"arn:aws:iot:*:*:topicfilter/{topic}",
            },
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


received_all_event = threading.Event()


## test publish
print('Begin Publish')
for i in range (3):
    data = "{} [{}]".format('Hello World', i+1)
    message = {"message" : data}
    mqtt_connection.publish(topic=topic, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
    print("Published: '" + json.dumps(message) + "' to the topic: " + topic)
    t.sleep(0.1)
print('Publish End')


def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))


print("Subscribing to topic '{}'...".format(topic))
subscribe_future, packet_id = mqtt_connection.subscribe(
    topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_message_received
)

subscribe_result = subscribe_future.result()
print("Subscribed with {}".format(str(subscribe_result['qos'])))

received_all_event.wait()
