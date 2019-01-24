import json
import socket
import threading
from log import *
from utils import *


class End:
	"""
	终端, 客户端与服务端的父类
	"""
	def __init__(self):
		self.tcp_socket = socket.socket(type=socket.SOCK_STREAM)
		self.udp_socket = socket.socket(type=socket.SOCK_DGRAM)
		self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

	@staticmethod
	def encode(data):
		try:
			return json.dumps(data).encode('utf-8') if isinstance(data, dict) and TYPE in data else b''
		except:
			return b''

	@staticmethod
	def decode(raw_data):
		try:
			data = json.loads(raw_data.decode('utf-8'))
			return data if isinstance(data, dict) and TYPE in data else None
		except:
			return None

	def broadcast_udp(self, data):
		raw_data = self.encode(data)
		if raw_data:
			t = data[TYPE]
			try:
				debug('about to broadcast {} in udp'.format(t))
				for port in PORT_RANGE:
					self.udp_socket.sendto(raw_data, ('255.255.255.255', port))
			except OSError as e:
				if e.args[0] == 9:
					debug('failed to broadcast {} in udp because socket has been closed'.format(t))
				else:
					raise e
			else:
				debug('broadcasted {} in udp'.format(t))

	def send_udp(self, data, address):
		raw_data = self.encode(data)
		if raw_data:
			t = data[TYPE]
			addr = self.format_address(address)
			action = 'send {} in udp to {}'.format(t, addr)
			debug(about_to(action))
			try:
				self.udp_socket.sendto(raw_data, address)
			except OSError as e:
				if e.args[0] == 9:
					debug(about_to_stop(action, SOCKET_CLOSED))
				else:
					raise e
			else:
				debug(succeed_to(action))

	def recv_udp(self):
		action = 'receiving udp'
		debug(about_to(start(action)))
		try:
			udp_address = self.udp_socket.getsockname()
		except OSError as e:
			if e.args[0] == 9:
				debug(about_to_stop(start(action), SOCKET_CLOSED))
			else:
				raise e
		else:
			addr = self.format_address(udp_address)
			action = '{} on {}'.format(action, addr)
			debug(started(action))
			while True:
				try:
					raw_data, address = self.udp_socket.recvfrom(65535)
				except OSError as e:
					if e.args[0] == 9:
						debug(about_to_stop(action, SOCKET_CLOSED))
						break
					else:
						raise e
				else:
					data = self.decode(raw_data)
					if data:
						self.handle_udp(data, address)
			debug(stopped(action))

	def handle_udp(self, data, address):
		raise Exception

	def send_tcp(self, data, remote_socket: socket.socket):
		raw_data = self.encode(data)
		if raw_data:
			t = data[TYPE]
			address = remote_socket.getpeername()
			addr = self.format_address(address)
			action = 'send {} in tcp to {}'.format(t, addr)
			debug(about_to(action))
			size = len(raw_data)
			raw_size = b''
			for i in range(LENGTH_SIZE):
				raw_size = bytes([size % 0x100]) + raw_size
				size //= 0x100
			remote_socket.sendall(raw_size+raw_data)
			debug(succeed_to(action))

	def recv_tcp(self, remote_socket: socket.socket):
		address = remote_socket.getpeername()
		addr = self.format_address(address)
		action = 'receiving tcp from {}'.format(addr)
		debug(started(action))
		while True:
			try:
				raw_size = remote_socket.recv(LENGTH_SIZE)
			except OSError as e:
				if e.args[0] == 9:
					debug(about_to_stop(action, SOCKET_CLOSED))
					break
				else:
					raise e
			else:
				size = int.from_bytes(raw_size, 'big')
				raw_data = remote_socket.recv(size)
				data = self.decode(raw_data)
				if data:
					self.handle_tcp(data, remote_socket)
		debug(stopped(action))

	def handle_tcp(self, data, remote_socket):
		raise Exception

	@staticmethod
	def format_address(address):
		return '{0[0]}:{0[1]}'.format(address)


class Client(End):
	"""
	客户端
	"""
	def __init__(self):
		super().__init__()
		# 广播CLIENT_HELLO
		data = {TYPE: CLIENT_HELLO}
		self.broadcast_udp(data)
		# 新线程中循环接受并处理UDP数据
		threading.Thread(target=self.recv_udp).start()

	def handle_udp(self, data, address):
		t = data[TYPE]
		addr = self.format_address(address)
		debug('received {} from {}'.format(t, addr))
		if t == SERVER_HELLO:
			address = address[0], data[PORT]
			# for test
			# 先连接, 连接后发送若干MESSAGE并正常disconnect
			# 期间每次发送前有一定几率直接结束(模拟断线)
			self.connect(address)
			for i in range(randint(0, 5)):
				if random() <= 0.2:
					self.tcp_socket.close()
					self.udp_socket.close()
					break
				data = {
					TYPE: MESSAGE,
					CONTENT: i
				}
				self.send_tcp(data, self.tcp_socket)
			else:
				self.disconnect()

	def handle_tcp(self, data, remote_socket):
		pass

	def connect(self, address):
		self.tcp_socket.connect(address)
		addr = self.format_address(address)
		debug('connected with {}'.format(addr))
		threading.Thread(target=self.recv_tcp, args=(self.tcp_socket,)).start()

	def disconnect(self):
		address = self.tcp_socket.getpeername()
		addr = self.format_address(address)
		data = {TYPE: DISCONNECT}
		self.send_tcp(data, self.tcp_socket)
		self.tcp_socket.close()
		debug('disconnected with {}'.format(addr))
		self.tcp_socket = socket.socket(type=socket.SOCK_STREAM)


class Server(End):
	"""
	服务端
	"""
	def __init__(self):
		super().__init__()

		# 已连接的客户端
		self.connected_client_socket_set = set()

		# 绑定一个TCP端口, 并在新线程中循环接受客户端的连接
		self.bind_tcp()
		threading.Thread(target=self.accept).start()

		# 广播SERVER_HELLO
		port = self.get_tcp_port()
		if port:
			data = {
				TYPE: SERVER_HELLO,
				PORT: port
			}
			self.broadcast_udp(data)
		# 在新线程中循环接受并处理UDP数据
		threading.Thread(target=self.recv_udp).start()

	def handle_udp(self, data, address):
		t = data[TYPE]
		addr = self.format_address(address)
		debug('received {} from {}'.format(t, addr))
		if t == CLIENT_HELLO:
			# 定向发送一个SERVER_HELLO告知对方自己的存在
			port = self.get_tcp_port()
			if port:
				data = {
					TYPE: SERVER_HELLO,
					PORT: port
				}
				self.send_udp(data, address)

	def handle_tcp(self, data, remote_socket):
		t = data[TYPE]
		address = remote_socket.getpeername()
		addr = self.format_address(address)
		debug('received {} from {}'.format(t, addr))
		if t == DISCONNECT:
			self.disconnect(remote_socket)
		elif t == MESSAGE:
			# for test
			# 以一定几率直接关闭socket
			if random() <= 0.2:
				self.disconnect(remote_socket)

	def get_tcp_port(self):
		"""
		获取所监听的TCP端口号
		若tcp_socket已关闭, 则返回0
		"""
		try:
			port = self.tcp_socket.getsockname()[1]
		except OSError as e:
			if e.args[0] == 9:
				port = 0
			else:
				raise e
		return port

	def bind_tcp(self):
		self.tcp_socket.bind(('0.0.0.0', 0))
		self.tcp_socket.listen(BACK_LOG)
		port = self.get_tcp_port()
		if port:
			debug('bound tcp on {}'.format(port))

	def accept(self):
		action = 'accepting'
		debug(started(action))
		while True:
			try:
				client_socket, _ = self.tcp_socket.accept()
			except OSError as e:
				if e.args[0] == 9:
					break
			else:
				address = client_socket.getpeername()
				addr = self.format_address(address)
				info('connected with {}'.format(addr))
				self.connected_client_socket_set.add(client_socket)
				threading.Thread(target=self.recv_tcp, args=(client_socket,)).start()
		debug(stopped(action))

	def disconnect(self, client_socket):
		address = client_socket.getpeername()
		addr = self.format_address(address)
		client_socket.close()
		self.connected_client_socket_set.remove(client_socket)
		debug('disconnected with {}'.format(addr))
