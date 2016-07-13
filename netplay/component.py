import bge
import logging

net = bge.logic.netplay


class NetComponent:
    def start(self, args):
        # Netplay needs to be initialized before the scene loads
        if net.server:
            self.permissions = []  # Client IDs allowed to send input
            self.net_id = 0  # FIXME
            self.setup()
            self.start_server()
            buff = self.get_setup_data()
            if buff is None:
                logging.error('No setup data')
            else:
                # Send it
                for c in net.clients:
                    if c is not None:
                        c.send_reliable(buff)
        else:
            self.permission = False
            ob = self.object
            if '_net_table' in ob:
                self.setup()
                self.start_client(ob['_net_table'])
            else:
                # On clients, all network-enabled objects placed in the editor
                # are initially removed.  The server will re-add as needed.
                # It's workarounds like this that make me question the
                # validity of such a project.
                ob.endObject()

    def setup(self):
        # Stuff to call on both client and server
        return

    def start_server(self):
        return

    def update(self):
        self.update_both()

        if net.server:
            self.update_server()
        else:
            self.update_client()

    def update_both(self):
        return

    def update_server(self):
        return

    def update_client(self):
        return

    def get_setup_data(self):
        # This gets called when we need data to spawn the object client-side
        # Typically when the object is first created & when new clients connect
        """
        table = packer.Table('NameOfTable')

        # Netplay needs 'id' in the component state table
        table.set('id', self.net_id)

        # Everything else can be whatever
        table.set('name', self.playername)

        pos = self.object.worldPosition
        table.set('x', pos[0])
        table.set('y', pos[1])
        table.set('z', pos[2])

        return packer.to_bytes(table)
        """
        return None
