## WEB INTERFACE / DATABASE THING MIGHT BE VERY BROKEN RIGHT NOW


import socket
import json
import time
import threading
import sqlite3


"""
Game servers both register and update their data
by sending a dict of strings (see Game.info below)
Invalid keys will be ignored.
Not all keys need to be sent.  In fact, an empty dict will also work,
merely updating the timestamp so it doesn't time out.
"""

DATABASE = 'master.db'


class Game:
    def __init__(self, ip, port):
        self.timestamp = time.time()
        self.ip = ip
        self.port = port
        self.info = {}
        self.info['Name'] = 'unnamed server'
        self.info['Map'] = ''
        self.info['TotalPlayers'] = '-1'
        self.info['MaxPlayers'] = '-1'
        self.info['PlayerList'] = ''

    def update(self, data):
        info = self.info

        for key, value in list(data.items()):
            if type(key) is not str:
                print ("Invalid key type")
                return False

            if type(value) is not str:
                print ("Invalid value type")
                return False

            if not (key in info):
                print ("Key does not exist")
                return False

            info[key] = value

        self.timestamp = time.time()

        print ("FIXME - index by IP and port")
        self.remove_from_db()
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        q = 'insert into servers (name, map, totalPlayers, maxPlayers, playerList) values ("{}", "{}", {}, {}, "{}")'.format(info['Name'], info['Map'], int(info['TotalPlayers']), int(info['MaxPlayers']), info['PlayerList'])
        cursor.execute(q)
        db.commit()
        return True

    def remove_from_db(self):
        print ("FIXME - delete by IP and port")
        info = self.info
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        q = 'DELETE FROM servers WHERE name = "{}"'.format(info['Name'])
        cursor.execute(q)
        db.commit()


class ClientThread(threading.Thread):
    def __init__(self, master, con, addr):
        threading.Thread.__init__(self)
        self.master = master
        self.con = con
        self.addr = addr
        self.timeout = time.time() + 10.0
        #self.start()
        self.run()

    def validate(self, data):
        if type(data) is not list:
            print ("Invalid data type")
            return False

        if len(data) < 2:
            print ("Data too short")
            return False

        if type(data[0]) is not int:
            print ("Wrong port number type")
            return False

        if type(data[1]) is not dict:
            print ("Wrong info type")
            return False

        return True

    def process_server(self, ip, bdata):
        try:
            data = json.loads(bdata)
        except:
            return False

        if not self.validate(data):
            return False

        port = data[0]
        info = data[1]

        for g in self.master.game_list:
            if (g.ip == ip) and (g.port == port):
                if 'end' in info:
                    # Game has ended, remove it
                    self.master.game_list.remove(g)
                else:
                    g.update(info)

                return True

        # Add new
        g = Game(ip, port)
        if g.update(info):
            self.master.game_list.append(g)
            return True

        else:
            return False

    def process_client(self):
        data = []
        for g in self.master.game_list:
            data.append([g.ip, g.port, g.info])

        bdata = bytes(json.dumps(data), 'UTF-8')
        bdata += b'\0'
        self.con.sendall(bdata)

    def run(self):
        currentdata = b''
        finaldata = None
        timeout = time.time() + 5.0

        done = False
        while not done:
            try:
                #datastring = bytes.decode(self.con.recv(1024), 'UTF-8')
                databytes = self.con.recv(1024)
                if databytes == b'':
                    break

                currentdata += databytes.split(b'\0')[0]
                if b'\0' in databytes:
                    finaldata = bytes.decode(currentdata, 'UTF-8')
                    done = True
                    break

                timeout = time.time() + 5.0

            except:
                if time.time() > timeout:
                    print ("Never received EOF, timing out")
                    self.con.close()
                    return False

        if finaldata is not None:
            if finaldata == "":
                # Client requesting server list
                print ("Processing client")
                self.process_client()
            else:
                # Server heartbeat
                print ("Processing server")
                self.process_server(self.addr[0], finaldata)

        self.con.close()
        print ("Closing connection")


class Master:
    def run(self):
        # Wipe the database
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute("DELETE FROM servers")
        db.commit()

        self.game_list = []

        HOST = ''
        PORT = 4000
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        s.setblocking(0)

        print ("Server started")

        """
        for i in range(0, 30):
            g = Game('127.0.0.1', '5555')
            g.info['Map'] = 'template'

            g.info['Name'] += str(i)

            g.timestamp += 3600.0
            self.game_list.append(g)
        """

        while True:
            try:
                con, addr = s.accept()
            except:
                con = None
                time.sleep(0.5)

            if con is not None:
                print ('Connection received')
                ClientThread(self, con, addr)

            timeout = time.time() - 120.0
            for g in self.game_list:
                if timeout > g.timestamp:
                    g.remove_from_db()
                    self.game_list.remove(g)
                    break


if __name__ == '__main__':
    app = Master()
    app.run()
