水位計測装置

- programs -
 controller.py  : ポンプを制御するプログラム
 servo.py       : サーボを制御するプログラム
 api.py         : 水位を制御する WebAPI を提供するプログラム
 manualinput.py : ポンプとサーボを直接制御するウェブUI
 awsclient.py   : 水位パイプの状態（水位と注水方向)をAWS IoT に送信するプログラム

- sh -
 runpump.sh     : api.py を自動で実行するスクリプト

- configs -
 AmazonRootCA1.pem : AWSへログインするためのルート証明書
 aws.ini           : AWSへログインするための設定ファイル
 requirements.txt  : 水位計測装置プログラム群を動作させるための必要パッケージ

- How to run -
WebAPI -> WebUI の順に起動 
 > python3 api.py
 > python3 manualinput.py
 
