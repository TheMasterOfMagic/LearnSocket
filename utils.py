PORT_RANGE = range(49152, 65535 + 1)
BACK_LOG = 5
LENGTH_SIZE = 2

CLIENT_HELLO = 'CLIENT_HELLO'
SERVER_HELLO = 'SERVER_HELLO'
DISCONNECT = 'DISCONNECT'
MESSAGE = 'MESSAGE'
CONTENT = 'CONTENT'
TYPE = 'TYPE'
PORT = 'PORT'


SOCKET_CLOSED = 'socket has been closed'


def about_to(action: str):
	return 'about to {}'.format(action)


def succeed_to(action: str):
	return 'succeed to {}'.format(action)


def about_to_stop(action: str, because: str = None):
	rv = 'about to stop {}'.format(action)
	if because:
		rv += ' because {}'.format(because)
	return rv


def start(action: str):
	return 'start {}'.format(action)


def started(action: str):
	return 'started {}'.format(action)


def stopped(action: str):
	return 'stopped {}'.format(action)


# for test
from time import sleep
from random import randint, random
