#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                double = False
                for client in self.server.clients:
                    if (login  == client.login) and login != None:
                        self.transport.write(f"Логин {login} занят, попробуйте другой\n".encode())
                        self.connection_lost("login duplicate")
                        double = True
                if double == False:
                    self.login = login
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                        )
                    self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        print(f"message: {message}")
        for user in self.server.clients:
            user.transport.write(message.encode())
        
        self.server.messages.append(message.replace("login:", "").replace("\r\n", ""))
        if (len(self.server.messages) > 10):
            self.server.messages = self.server.messages[1:]
    
    def send_history(self):
        for message in self.server.messages:
            self.transport.write(f"{message}\n".encode())
            

class Server:
    clients: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")