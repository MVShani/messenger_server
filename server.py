"""
Серверное приложение для соединений

"""
# подключаем библиотеки
import asyncio
from asyncio import transports
from typing import Optional

global history_cache
history_cache: list
history_cache = []

class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: asyncio.transports.Transport
    other_logins: list

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None
        self.other_logins = []
        self.login_try = ""

    def data_received(self, data: bytes):
        # print(data)

        decoded = data.decode()  # декодирование байтстроки в текст
        print(decoded)

        if self.login is None:

            # поступят данные вида "login: User"
            # и мы сделаем из них свой логин
            if decoded.startswith("login:"):
                self.login_try = decoded.replace("login:", "").replace("\r\n", "")
                # \r - переход в начало строки
                # \n - переход в новую строку
                if self.login_try not in self.other_logins:
                    self.login = self.login_try

                    self.transport.write(
                        f"Привет, {self.login}!\r\n".encode()
                    )
                    self.history()

                else:
                    self.transport.write(
                        f" Логин <{self.login_try}> занят! \r\n Введите уникальный логин!".encode()
                    )

        else:
            self.send_message(decoded)

            if len(history_cache) >= 10:
                history_cache.remove(history_cache[0])
                history_cache.append(f"<{self.login}> {decoded}")
            else:
                history_cache.append(f"<{self.login}> {decoded}")

        if self.login is None:
            # создадим список других логинов
            # и покажем новому пользователю занятые имена
            self.other_logins = []
            for client in self.server.clients:
                if client.login != None:
                    self.other_logins.append(client.login)
                else:
                    pass
            if self.other_logins:
                self.transport.write(f"Занятые логины: {self.other_logins}\r\n".encode())
                # призыв создать логин
                self.transport.write(
                    "Введите незанятый логин командой: <login: ...>\r\n".encode()
                )
            else:
                self.transport.write(f"Все логины свободны!\r\n".encode())
                # призыв создать логин
                self.transport.write(
                    "Введите логин командой: <login: ...>\r\n".encode()
                )

    def history(self):
        # если есть предыдущие сообщения, покажем до 10 последних
        if len(history_cache) != 0:
            self.transport.write(
                f"Предыдущие {len(history_cache)} сообщений:\r\n".encode()
            )
            for cache_message in history_cache:
                self.transport.write(
                    f"{cache_message}\r\n".encode()
                )
        else:
            pass


    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")


    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
