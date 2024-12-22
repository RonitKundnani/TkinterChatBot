import threading
import socket
import argparse
import sys
import tkinter as tk
from tkinter import Scrollbar

class Send(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name

    def run(self):
        while True:
            sys.stdout.write('{}: '.format(self.name))
            sys.stdout.flush()
            message = sys.stdin.readline().strip()

            if message == "QUIT":
                self.sock.sendall(f'Server: {self.name} has left the chat.'.encode('ascii'))
                break
            else:
                self.sock.sendall(f'{self.name}: {message}'.encode('ascii'))

        print('\nQuitting')
        self.sock.close()
        sys.exit(0)

class Receive(threading.Thread):
    def __init__(self, sock, messages):
        super().__init__()
        self.sock = sock
        self.messages = messages

    def run(self):
        while True:
            try:
                message = self.sock.recv(1024).decode('ascii')
                if message:
                    self.messages.after(0, self.messages.insert, tk.END, message)
                    self.messages.after(0, self.messages.yview, tk.END)  # Auto-scroll to the bottom
                else:
                    print('\nNo. We have lost connection to the server!')
                    print('\nQuitting....')
                    self.sock.close()
                    sys.exit(0)
            except ConnectionResetError:
                print('\nConnection reset by server!')
                self.sock.close()
                sys.exit(0)

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None
        self.messages = None

    def start(self):
        print(f'Trying to connect to {self.host}:{self.port}...')
        self.sock.connect((self.host, self.port))
        print(f'Successfully connected to {self.host}:{self.port}')
        print()
        self.name = input("Your name: ")
        print()
        print(f'Welcome, {self.name}! Getting ready to send and receive messages...')

        receive = Receive(self.sock, self.messages)
        receive.start()

        send = Send(self.sock, self.name)
        send.start()

        self.sock.sendall(f'Server: {self.name} has joined the chat. Say whatsup!'.encode('ascii'))
        print("\rReady!! Leave the chatroom anytime by typing 'QUIT'\n")
        print('{}:'.format(self.name), end='')
        return receive

    def send(self, textInput):
        message = textInput.get()
        textInput.delete(0, tk.END)
        self.messages.insert(tk.END, f'{self.name}: {message}')
        self.messages.yview(tk.END)  # Auto-scroll to the bottom

        if message == "QUIT":
            self.sock.sendall(f'Server: {self.name} has left the chat.'.encode('ascii'))
            print('\nQuitting....')
            self.sock.close()
            sys.exit(0)
        else:
            self.sock.sendall(f'{self.name}: {message}'.encode('ascii'))

def main(host, port):
    client = Client(host, port)
    receive = client.start()

    window = tk.Tk()
    window.title("Chatroom")

    fromMessage = tk.Frame(master=window)
    scrollBar = Scrollbar(master=fromMessage)
    messages = tk.Listbox(master=fromMessage, yscrollcommand=scrollBar.set)
    scrollBar.config(command=messages.yview)
    scrollBar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
    messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    client.messages = messages
    receive.messages = messages

    fromMessage.grid(row=0, column=0, columnspan=2, sticky="nsew")
    fromEntry = tk.Frame(master=window)
    textInput = tk.Entry(master=fromEntry)

    textInput.pack(fill=tk.BOTH, expand=True)
    textInput.bind("<Return>", lambda x: client.send(textInput))
    textInput.insert(0, "Write your message here.")

    btnSend = tk.Button(master=window, text='Send', command=lambda: client.send(textInput))
    fromEntry.grid(row=1, column=0, padx=10, sticky="ew")
    btnSend.grid(row=1, column=1, padx=10, sticky="ew")

    window.rowconfigure(0, minsize=500, weight=1)
    window.rowconfigure(1, minsize=50, weight=0)
    window.columnconfigure(0, minsize=500, weight=1)
    window.columnconfigure(1, minsize=200, weight=0)

    window.mainloop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chat Client")
    parser.add_argument('host', help='Host to connect to')
    parser.add_argument('-p', metavar='PORT', type=int, default=1068, help='TCP port (default 1068)')

    args = parser.parse_args()

    main(args.host, args.p)
