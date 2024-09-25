# -*- coding: utf-8 -*-
"""
matplotlibでリアルタイムプロットする例

無限にsin関数をplotし続ける
"""
from __future__ import unicode_literals, print_function
import math
import numpy as np
import matplotlib.pyplot as plt
import awsclient
import argparse

parser = argparse.ArgumentParser(description="realtime plot app on a web browser")
parser.add_argument('-d', '--device', type=str, default='/dev/serial0', help='a device file connected to arduino')
args = parser.parse_args()

def pause_plot():

    readSer = awsclient.Serial(args.device, 9600, timeout=3)
    value = 0.0

    fig, ax = plt.subplots(1, 1)
    # ax.set_aspect(0.5)
    #x = np.arange(-np.pi, np.pi, 0.1)
    x = np.arange(0, 512, 0.5)
    y = np.arange(0, 1024, 1)
    # 初期化的に一度plotしなければならない
    # そのときplotしたオブジェクトを受け取る受け取る必要がある．
    # listが返ってくるので，注意
    lines, = ax.plot(x, y)

    # x 軸のラベルを設定する。
    ax.set_xlabel("Time (second)")

    # y 軸のラベルを設定する。
    ax.set_ylabel("Water Level")

    # タイトルを設定する。
    ax.set_title("Water Level Measurement")

    # ここから無限にplotする
    while True:
        # plotデータの更新
        value = float(readSer.readline().strip())
        #print(math.pow(value * 0.01, 2))
        print(value)
        x += 0.1
        y = np.delete(y, 0, None)
        #y = np.append(y, math.pow(value * 0.01, 2))
        y = np.append(y, value)

        # 描画データを更新するときにplot関数を使うと
        # lineオブジェクトが都度増えてしまうので，注意．
        #
        # 一番楽なのは上記で受け取ったlinesに対して
        # set_data()メソッドで描画データを更新する方法．
        lines.set_data(x, y)

        # set_data()を使うと軸とかは自動設定されないっぽいので，
        # 今回の例だとあっという間にsinカーブが描画範囲からいなくなる．
        # そのためx軸の範囲は適宜修正してやる必要がある．
        ax.set_xlim((x.min(), x.max()))

        # 一番のポイント
        # - plt.show() ブロッキングされてリアルタイムに描写できない
        # - plt.ion() + plt.draw() グラフウインドウが固まってプログラムが止まるから使えない
        # ----> plt.pause(interval) これを使う!!! 引数はsleep時間
        plt.pause(.01)

if __name__ == "__main__":
    pause_plot()
