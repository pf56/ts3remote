import npyscreen
import api

global API


class MainForm(npyscreen.Form):
    def create(self):
        npyscreen.setTheme(npyscreen.Themes.ColorfulTheme)
        self.servername = API.get_servervariables("virtualserver_name")
        self.wgtree = self.add_widget(npyscreen.MLTree)
        self.keypress_timeout = 5

        self.channels = API.get_channels()

        self.channel_map = {}
        self.__build_map(self.channels, self.channel_map)

    def while_waiting(self):
        for channel in list(self.channel_map.values()):
            del channel.clients[:]

        self.clients = API.get_clients()

        for client in self.clients:
            self.channel_map[client.cid].clients.append(client)

        treedata = npyscreen.TreeData(content=self.servername,
                                      ignore_root=False)
        self.__build_tree(self.channels, treedata)

        self.wgtree.values = treedata
        self.wgtree.display()

    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def __build_map(self, channels, hashmap):
        for channel in channels:
            hashmap[channel.cid] = channel
            self.__build_map(channel.children, hashmap)

    def __build_tree(self, channels, root_node):
        for channel in channels:
            td = root_node.new_child(content=channel.name)
            [td.new_child(content=client.name) for client in channel.clients]
            self.__build_tree(channel.children, td)


class TS3Remote(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", MainForm, name="TS3 Remote")


if __name__ == "__main__":
    API = api.api()
    API.connect()
    App = TS3Remote().run()
    API.close()
