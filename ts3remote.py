import api
import curses

global API


def draw_channels(window, channels, x, y):
    total = 0

    for channel in channels:
        if y >= curses.LINES:
            break

        window.addstr(y, x, channel.name, curses.A_DIM)
        y += 1
        total += 1

        for client in channel.clients:
            window.move(y, x + 2)

            if client.input_muted:
                window.addstr("[I]", curses.color_pair(1))

            if client.output_muted:
                window.addstr("[O]", curses.color_pair(1))

            if client.talking:
                window.addstr(client.name, curses.A_BOLD)
            else:
                window.addstr(client.name)

            y += 1
            total += 1

        y += draw_channels(window, channel.children, x + 2, y)

    return total


def build_map(channels, hashmap={}):
    for channel in channels:
        hashmap[channel.cid] = channel
        hashmap.update(build_map(channel.children, hashmap))

    return hashmap


def main(stdscr):
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    stdscr.refresh()

    win = curses.newwin(curses.LINES, curses.COLS - 2, 0, 1)
    win.box()
    channels = API.get_channels()
    channel_map = build_map(channels)

    while True:
        win.clear()
        win.box()

        clients = API.get_clients()

        for client in clients:
            channel_map[client.cid].clients.append(client)

        draw_channels(win, channels, 2, 2)

        for channel in list(channel_map.values()):
            del channel.clients[:]

        win.refresh()
        # c = stdscr.getkey()

        # if c == "q":
        #    break

if __name__ == "__main__":
    API = api.api()
    API.connect()
    curses.wrapper(main)
    API.close()
