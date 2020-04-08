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

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()
        if self.login is not None:
            self.send_massage(decoded)
        else:
            if decoded.startswith("login:"):
                test_login = decoded.replace("login:", "").replace("\r\n", "")
                if test_login not in self.client_login_list:
                    self.login = test_login
                    self.client_login_list.append(self.login)
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
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

    def send_massage(self, content: str):
        massage = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.transport.write(massage.encode())


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
