import sys
import socket


class api:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, address="localhost", port=25639):
        try:
            self.sock.connect((address, port))
            self.sock.settimeout(0.5)
        except:
            print("Unable to connect.")
            sys.exit()

        print("Successfully connected.")
        self.receive()

    def receive(self):
        data = ""

        while True:
            try:
                data += self.sock.recv(4096).decode("utf-8")
            except socket.error as err:
                if type(err) != socket.timeout:
                    print("Error while receiving from server: {}".format(err))
                    sys.exit(0)
                break

        lines = data.splitlines()
        lines = list(filter(None, lines))

        if len(lines) == 0:
            return (None, None)

        return (lines[:-1], self.__checkForError(lines))

    def send(self, command):
        command += "\r\n"
        self.sock.sendall(command.encode("utf-8"))

    def __unescape(self, string):
        string = string.replace("\\s", " ")
        string = string.replace("\\p", "|")
        string = string.replace("\\/", "/")
        return string

    def __getParameters(self, *parameters):
        data = " ".join(parameters)
        data = data.split()
        parameters = {}

        for pair in data:
            s = pair.split("=", 1)

            if len(s) == 2:
                parameters[s[0]] = self.__unescape(s[1])

        if len(parameters) == 1:
            return list(parameters.values())[0]

        return parameters

    def __checkForError(self, lines):
        if not lines[-1].startswith("error "):
            return None

        error_data = self.__getParameters(lines[-1])
        error_id = int(error_data["id"])

        if error_id == 0:  # error: ok
            return None

        error_message = error_data["msg"].replace("\s", " ")
        print("Error: {0} - {1}".format(error_id, error_message))
        return (error_id, error_message)

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        print("Connection closed.")

    def get_servervariables(self, *properties):
        self.send("servervariable " + " ".join(properties))
        lines, error = self.receive()

        if error is not None:
            return None

        return self.__getParameters(*lines)

    def get_clients(self):
        self.send("clientlist -voice")
        response, error = self.receive()

        if error is not None:
            return None

        response = response[0].split(sep="|")
        clients = []

        for r in response:
            param = self.__getParameters(r)

            if param["client_type"] != "0":
                continue

            client = Client(param["clid"], param["cid"],
                            param["client_nickname"],
                            param["client_flag_talking"],
                            param["client_input_muted"],
                            param["client_output_muted"])
            clients.append(client)

        return clients

    def get_channels(self):
        self.send("channellist")
        response, error = self.receive()

        if error is not None:
            return None

        response = response[0].split(sep="|")
        channels = {}

        for r in response:
            param = self.__getParameters(r)
            channel = Channel(param["cid"], param["pid"],
                              param["channel_order"], param["channel_name"])

            channels[channel.cid] = channel

        helper = []
        for channel in channels.values():
            if channel.pid == "0":
                continue

            channels[channel.pid].children.append(channel)
            helper.append(channel.cid)

        for cid in helper:
            channels.pop(cid)

        return self.__sort_channels(list(channels.values()))

    def __sort_channels(self, channels):
        if len(channels) < 1:
            return []

        sort = {}
        sorted_list = []

        for channel in channels:
            channel.children = self.__sort_channels(channel.children)
            sort[channel.order] = channel

        sorted_list.append(sort["0"])
        next_order = sort["0"].cid

        while next_order in sort:
            c = sort[next_order]
            sorted_list.append(c)
            next_order = c.cid

        return sorted_list


class Channel:

    def __init__(self, cid, pid, order, name):
        self.cid = cid
        self.pid = pid
        self.order = order
        self.name = name
        self.children = []
        self.clients = []

    def get_name(self):
        return self.name

    def sort_children(self):
        if self.children == []:
            return

        self.children = sorted(self.children, key=lambda c: c.order)

    def __repr__(self):
        return "cid:{0},pid:{1},order:{2},name:{3},children:{4}"\
                .format(self.cid, self.pid, self.order, self.name,
                        self.children)


class Client:

    def __init__(self, clid, cid, name, talking=False, input_muted=False,
                 output_muted=False):
        self.clid = clid
        self.cid = cid
        self.name = name
        self.talking = int(talking)
        self.input_muted = int(input_muted)
        self.output_muted = int(output_muted)

    def __repr__(self):
        return "clid:{0},cid{1},name:{2}"\
                .format(self.clid, self.cid, self.name)
