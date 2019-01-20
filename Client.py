import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))

true = True


def send_func(sock):
	global true
	while true:
		message = input()
		if true:
			sock.send(message.encode('utf8'))
		if message == 'exit':
			true = False
			s.close()


def recv_func(sock):
	global true
	while true:
		message = sock.recv(65536).decode('utf8')
		if message == 'exit':
			true = False
			s.close()
			info = '[System] remote server has left'
		else:
			info = message
		print(info)


send_thread = threading.Thread(target=send_func, args=(s,))
recv_thread = threading.Thread(target=recv_func, args=(s,))
send_thread.start()
recv_thread.start()
send_thread.join()
recv_thread.join()

s.close()
