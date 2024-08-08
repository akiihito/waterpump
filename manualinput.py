from flask_socketio import SocketIO
from flask import Flask, render_template
from fastapi.responses import RedirectResponse



if __name__ == '__main__':
    app = Flask(__name__)
    socketio = SocketIO(app)

    @app.get('/')
    def redirect():
        return RedirectResponse('/manual')

    @app.route("/manual")
    def hello_world():
        return render_template('input.html')
    
    # With debug mode on, print message in Worker class will be printed twice.
    # https://stackoverflow.com/questions/57344224/thread-is-printing-two-times-at-same-loop
    #app.run(host="0.0.0.0", port=5000, debug=True)
    socketio.run(app, host="0.0.0.0", port=22331, allow_unsafe_werkzeug=True)