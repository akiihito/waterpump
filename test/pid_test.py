import matplotlib.pyplot as plt
import ipywidgets
import statistics

# ------------------------------- ウィジェット，インタラクティブの設定関連 ------------------------------
# text widgetsを作成 -> Vboxに格納して縦に並べる
def generate_vbox_text_widget():
    text_widgets = []
    text_widgets.append(ipywidgets.FloatText(min=0.0, max=359.0)) # theta_start
    text_widgets.append(ipywidgets.FloatText(min=0.0, max=359.0)) # theta_goal
    text_widgets.append(ipywidgets.FloatText(min=0.0, max=100.0)) # offset
    text_widgets.append(ipywidgets.IntText(min=-360, max=360)) # time_length
    text_widgets.append(ipywidgets.FloatText(min=0.00, max=1.50)) # kp
    text_widgets.append(ipywidgets.FloatText(min=0.00, max=1.50)) # ki
    text_widgets.append(ipywidgets.FloatText(min=0.00, max=1.50)) # kd
    vox_text_widgets = ipywidgets.VBox(text_widgets)
    return vox_text_widgets

# slider widgetsを7個作成 -> Vboxに格納して縦に並べる．
def generate_vbox_slider_widget():
    slider_widgets = []
    slider_widgets.append(ipywidgets.FloatSlider(value=0.0, min=0.0, max=359.0, description = "theta_start", disabled=False))
    slider_widgets.append(ipywidgets.FloatSlider(value=90.0, min=0.0, max=359.0, description = "theta_goal", disabled=False))
    slider_widgets.append(ipywidgets.FloatSlider(value=0.0, min=0.0, max=100.0, step=0.01, description = "offset", disabled=False))
    slider_widgets.append(ipywidgets.IntSlider(value=150, min=0, max=2000, description = "time_length", disabled=False))
    slider_widgets.append(ipywidgets.FloatSlider(value=0.10, min=0.00, max=1.50, step=0.001, description = "kp", disabled=False))
    slider_widgets.append(ipywidgets.FloatSlider(value=0.50, min=0.00, max=1.50, step=0.001, description = "ki", disabled=False))
    slider_widgets.append(ipywidgets.FloatSlider(value=0.50, min=0.00, max=1.50, step=0.001, description = "kd", disabled=False))
    vox_slider_widgets = ipywidgets.VBox(slider_widgets)
    return vox_slider_widgets


# Box内の複数のwidetを連携させる（二つのbox内のwidgetの数が同じである必要あり）
def link_slider_and_text(box1, box2):
    for i in range(7):
      ipywidgets.link((box1.children[i], 'value'), (box2.children[i], 'value'))

# 結果を表示
def draw_interactive():
    # slider widgetを作成
    sliders = generate_vbox_slider_widget()
    # text widgetを作成
    texts = generate_vbox_text_widget()

    # slider widget と　posture widget を横に並べる
    slider_and_text = ipywidgets.Box([sliders, texts])

    # slider wiget と text widget を連携
    link_slider_and_text(sliders, texts)

    # main文にslider widgetsの値を渡す
    params = {}
    for i in range(7):
        params[str(i)] = sliders.children[i]
    final_widgets = ipywidgets.interactive_output(main, params)
    
    display(slider_and_text, final_widgets)

# -------------------------------------- PID制御関連 ----------------------------------------
def PID(kp, ki, kd, theta_goal, theta_current, error_sum, error_pre):
    error = theta_goal - theta_current# 偏差（error）を計算
    error_sum += error # 偏差の総和（積分）を計算
    error_diff = error-error_pre # PI制御からの追加：1時刻前の偏差と現在の偏差の差分（微分）を計算
    m = (kp * error) + (ki * error_sum) + (kd*error_diff) # 操作量を計算
    return m, error_sum, error

def main(*args, **kwargs):
    # 係数などの設定 --------------------
    # スライダーやテキストボックスから得られた数値を代入
    params = kwargs
    theta_start = params["0"]
    theta_goal = params["1"]
    offset = params["2"]
    time_length = params["3"]
    kp = params["4"]
    ki = params["5"]
    kd = params["6"]
    # その他初期設定
    error_sum = 0.0
    error_pre = 0.0
    theta_current = theta_start
    time_list = [0]
    theta_list = [theta_start]

    # PID制御 -----------------------
    cnt = 0
    mlist = []
    for time in range(1, time_length):
        m, error_sum, error = PID(kp, ki, kd, theta_goal, theta_current, error_sum, error_pre) # 操作量を計算
        theta_current += m # 現在角度に操作量を足す（実際は，この操作量をもとにモータを動かす）
        mlist.append(m)
        if len(mlist) > 10:
            print('[', cnt, ']', m, theta_current, statistics.stdev(mlist[-10:]))
        else:
            print('[', cnt, ']', m, theta_current, 'NaN')
        theta_current -= offset
        error_pre = error # 一時刻前の偏差として保存しておく（D制御用）
        time_list.append(time) # 描画用
        theta_list.append(theta_current) # 描画用
        cnt += 1

    # 描画
    plt.hlines([theta_goal], 0, time_length, "red", linestyles='dashed') #ゴールを赤色の点線で表示
    plt.plot(time_list, theta_list, label="PID", color="blue") # PID制御のグラフを描画
    plt.xlabel(r'$t$') 
    plt.ylabel(r'$\theta$') 
    plt.ylim(theta_start-20, theta_goal+60) # 大体の場合において，グラフが収まる範囲に設定（適当）
    plt.legend(loc='lower right') # 凡例を表示
    plt.title(r'final $\theta$={:.3g}'.format(theta_list[-1])) # タイトルに時間と角度を表示
    plt.show() # グラフの表示

# インタラクティブ描画実行
draw_interactive()