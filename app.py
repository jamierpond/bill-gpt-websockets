from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import time
from threading import Event
from billgpt.model import Transformer
from billgpt.data import TextDataset, BILL_PATH
import torch
from billgpt.train import FAUSTUS
from billgpt.infer import generate

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Keep track of connected clients
connected_clients = set()

# Event to control the thread
thread = None
thread_stop_event = Event()

def generate_ascii_stream():
    """Generate a continuous stream of ASCII patterns"""
    ds = TextDataset(BILL_PATH)
    input_tokens = ds.tokenizer.tokenize(FAUSTUS)
    input_tokens = torch.Tensor(input_tokens).int().unsqueeze(0)
    model = Transformer(vocab_size=ds.tokenizer.vocab_size)
    model.load_state_dict(torch.load("./billgpt/best-model.pth", weights_only=True, map_location=device))

    model.to(device)
    input_tokens = input_tokens.to(device)

    initial_context = input_tokens

    while not thread_stop_event.is_set():
        def emit(data):
            socketio.emit('ascii_stream', {'data': data})

        if connected_clients:  # Only emit if there are connected clients
            generate(model, initial_context, max_len=int(1e18), next_token_callback=emit)

        # Add some randomness to the timing
        time.sleep(random.uniform(0.5, 2))

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    global thread
    print('Client connected')

    client_id = request.sid
    connected_clients.add(client_id)
    print(f'Client connected: {client_id}')

    if thread is None:
        thread_stop_event.clear()
        thread = socketio.start_background_task(generate_ascii_stream)
        print("Started background task")

    emit('welcome', {'data': 'Welcome to BillGPT!'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    connected_clients.discard(client_id)
    print(f'Client disconnected: {client_id}')

    # If no more clients, stop the thread
    if not connected_clients:
        thread_stop_event.set()
        global thread
        thread = None
        print("Stopped ASCII generation thread")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
