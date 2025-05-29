import json
import threading
import configparser
import time
from uuid import uuid4

import boto3
from awscrt import auth, io, mqtt
from awsiot import mqtt_connection_builder, iotshadow

class AWSClient:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("aws.ini")

        account_id = config['auth']['account_id']
        cafile     = config['auth']['cafile']

        endpoint = config['iot']['endpoint']
        region   = config['iot']['region']
        self.topic    = config['iot']['topic']
        things   = config['iot']['things']

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

        self.mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
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

        connect_future = self.mqtt_connection.connect()
        connect_future.result()
        # shadow will be used for register_callback
        # shadow = iotshadow.IotShadowClient(mqtt_connection)
        print("Connected!")

    ## api.py クライアントで利用される AWS Client は、水位データの subscribe が必要ないので Callback を利用する必要はない
    ## 水位を sniffing する必要のあるのは PID 制御を実施している waterlevel controller
    def register_callback(fn, topic):
        print("not implemented yet")
        pass

    def send_supply(self):
        ## True means "supply"
        data = {"state":{"desired":{"direction":True}}}
        self.mqtt_connection.publish(topic=self.topic, payload=json.dumps(data), qos=mqtt.QoS.AT_LEAST_ONCE)
        print("Published: '" + json.dumps(data) + "' to the topic: " + self.topic)
    
    def send_drain(self):
        ## False means "drain"
        data = {"state":{"desired":{"direction":False}}}
        self.mqtt_connection.publish(topic=self.topic, payload=json.dumps(data), qos=mqtt.QoS.AT_LEAST_ONCE)
        print("Published: '" + json.dumps(data) + "' to the topic: " + self.topic)


if __name__ == "__main__":
    client = AWSClient()
    client.send_drain()
    time.sleep(1)
    client.send_supply()