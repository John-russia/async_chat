#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport
    client_login_list: list = []
    history: list = []

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        # print(data)
        # print(data.decode())
        if data != b'\r\n':  # этот if нужен, чтобы исключить лишние сообщения после нажатия Enter в Putty
            decoded = data.decode()
            if self.login is not None:
                self.send_message(decoded)
            else:
                if decoded.startswith("login:"):
                    test_login = decoded.replace("login:", "").replace("\r\n", "")
                    if test_login not in self.client_login_list:
                        self.login = test_login
                        self.client_login_list.append(self.login)
                        self.transport.write(
                            f"Привет, {self.login}!\n".encode()
                        )
                        self.send_history()
                    else:
                        self.transport.write(f"Логин: {test_login} занят, попробуйте другой\n".encode())
                else:
                    self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        if self in self.server.clients:
            self.server.clients.remove(self)
        if self.login in self.client_login_list:
            self.client_login_list.remove(self.login)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.write_history(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def write_history(self, message):
        message = message.replace("\n", "")
        if len(self.history) < 10:
            self.history.append(message)

        else:
            for i in range(len(self.history) - 1):
                self.history[i] = self.history[i + 1]
            self.history[len(self.history) - 1] = message

        # print("история:", self.history)

    def send_history(self):
        if len(self.history) > 0:
            self.transport.write(f"Последние 10 сообщений чата:\n".encode())
            for message in self.history:
                self.transport.write(f"{message}\n".encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()
        coroutine = await loop.create_server(
            self.build_protocol,
            "127.0.0.1",
            8888
        )
        print("Сервер запущен...")
        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
