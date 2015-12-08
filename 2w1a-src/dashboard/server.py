from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def connect():
    print('Client connected')

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

@socketio.on('simulation_end')
def simulation_end(data):
    emit('simulation_end', data, broadcast=True)

@socketio.on('new_generation')
def new_generation(data):
    emit('new_generation', data, broadcast=True)

@socketio.on('start_generation')
def start_generation(data):
    emit('start_generation', data, broadcast=True)




if __name__ == '__main__':
    socketio.run(app)
