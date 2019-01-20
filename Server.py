import socket
import threading

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('127.0.0.1', 9999))
server_socket.listen(256)

sock_pool = set()


def broadcast(info):
	for sock in sock_pool:
		sock.send(info.encode('utf-8'))
	print(info)


def recv_func(client_socket: socket.socket):
	ip, port = client_socket.getpeername()
	username = '{}'.format(port)
	info = '[Server] {} has joined the room'.format(username)
	broadcast(info)
	try:
		while True:
			message = client_socket.recv(65536).decode('utf8')
			if message == 'exit':
				sock_pool.remove(client_socket)
				client_socket.close()
				info = '[Server] {} left the room'.format(username)
				broadcast(info)
				break
			else:
				info = '[{}] {}'.format(username, message)
				broadcast(info)
	except:
		pass


def server_func():
	try:
		while True:
			client_socket, _ = server_socket.accept()
			sock_pool.add(client_socket)
			recv_thread = threading.Thread(target=recv_func, args=(client_socket,))
			recv_thread.start()
	except:
		pass


def command_func():
	while True:
		command = input().strip()
		if command == 'exit':
			broadcast('exit')
			for client_socket in sock_pool:
				client_socket.close()
			server_socket.close()
			break
		elif command == '':
			continue
		else:
			print('unknown command: {}'.format(command))


def main():
	server_thread = threading.Thread(target=server_func)
	command_thread = threading.Thread(target=command_func)
	server_thread.start()
	command_thread.start()
	server_thread.join()
	command_thread.join()


main()
