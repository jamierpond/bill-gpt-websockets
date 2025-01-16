from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import string
import time
from threading import Event

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Keep track of connected clients
connected_clients = set()

# Event to control the thread
thread = None
thread_stop_event = Event()

# ASCII art patterns you can use
ASCII_PATTERNS = [
    ".-*-.",
    "|[+]|",
    "<=>",
    "/-\\",
    "\\-/",
    "{o}",
    "[-]",
    "(~)",
]

def generate_ascii_stream():
    """Generate a continuous stream of ASCII patterns"""
    print("Starting ASCII generation thread...")
    while not thread_stop_event.is_set():
        if connected_clients:  # Only emit if there are connected clients
            # Create an interesting pattern
            pattern = random.choice(ASCII_PATTERNS)
            random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            stream_data = f"{pattern} {random_chars} {pattern}"

            # Emit to all connected clients
            socketio.emit('ascii_stream', {'data': stream_data})
            print(f"Emitted: {stream_data}")

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

    emit('welcome', {'data': 'Welcome to the ASCII stream!'})

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
