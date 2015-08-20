import struct

BOOL = '?'
CHAR = 'b'
UCHAR = 'B'
SHORT = 'h'
USHORT = 'H'
INT = 'i'
UINT = 'I'
LONG = 'q'
ULONG = 'Q'
FLOAT = 'f'
DOUBLE = 'd'
STRING = 'STRING'

# These variables go hand-in-hand
# See https://en.wikipedia.org/wiki/Integer_%28computer_science%29
STRING_LENGTH_TYPE = USHORT
STRING_LENGTH_MAX = 65535


def fromDataList(dataList):
    to_pack = []
    formatstring = '!H'
    for i in range(0, len(dataList)):
        formatstring += 'H'
        to_pack.append(len(dataList[i]))

    bdata = struct.pack(formatstring, len(dataList), *to_pack)
    for d in dataList:
        bdata += d

    return bdata


def toDataList(bdata):
    amount = struct.unpack('!H', bdata[:2])[0]
    #data = bdata[amount+1:]

    headerdata = bdata[2:]
    sizes = []
    i = 0
    while i < amount * 2:
        u = headerdata[:i + 2][i:]
        sizes.append(struct.unpack('!H', u)[0])
        i += 2

    dataList = []
    count = 0

    userdata = headerdata[amount * 2:]
    count = 0
    for s in sizes:
        d = userdata[:s + count][count:]
        dataList.append(d)
        count += s

    return dataList


class DataProcessor:

    def __init__(self, component, callback, datatypes, reliable, replicate,
                private, server_only):
        self.component = component
        self.callback = callback
        self.reliable = reliable
        self.replicate = replicate
        self.private = private
        self.server_only = server_only

        formatstring = '!'
        string_locations = []
        i = 0
        for d in datatypes:
            if d != STRING:
                formatstring += d
            else:
                string_locations.append(i)

            i += 1

        for i in string_locations:
            # Stores string length
            formatstring += STRING_LENGTH_TYPE

            # Could further optimize by ommitting last string length

        self.formatstring = formatstring
        self.string_locations = string_locations

    def getBytes(self, p_id, data):
        net_id = self.component.net_id

        header = struct.pack('!HH', net_id, p_id)
        if not len(self.string_locations):
            # Contains no strings
            st = struct.pack(self.formatstring, *data)
            return header + st
        else:
            # Push strings to the end
            strings = []
            packdata = []
            i = 0
            for d in data:
                if i in self.string_locations:
                    strings.append(d)
                else:
                    packdata.append(d)

                i += 1

            text = bytes()
            for s in strings:
                length = len(s)
                if length > STRING_LENGTH_MAX:
                    # String too long, truncate
                    print ("WARNING - Packed string was truncated, %d character limit" % STRING_LENGTH_MAX)
                    s = s[:STRING_LENGTH_MAX]
                    length = STRING_LENGTH_MAX

                packdata.append(length)
                text += bytes(s, 'UTF-8')

            st = struct.pack(self.formatstring, *packdata)
            st += text

            return header + st

    def getData(self, bdata):
        if not len(self.string_locations):
            # Contains no strings
            data = list(struct.unpack(self.formatstring, bdata))
            return data
        else:
            # Strings will be at the end
            # After unpacking, need to re-construct the list so strings
            # are in the correct location
            sz = struct.calcsize(self.formatstring)
            data = list(struct.unpack(self.formatstring, bdata[:sz]))
            text = bytes.decode(bdata[sz:], 'UTF-8')

            string_count = len(self.string_locations)
            len_count = string_count  # - 1

            ## Number shorts @ the end of data for string length
            #if len_count == 0:
            #    # Only one string
            #    data.insert(self.string_locations[0], text)
            #    return data
            #else:
            #    # Multiple strings

            # First get a list of strings
            lengths = data[(len(data) - len_count):]
            strings = []
            i = 0
            for L in lengths:
                #if i == len_count:
                #    # No len for the last string
                #    strings.append(text)
                #    text = ""
                #else:
                strings.append(text[:L])
                text = text[L:]
                i += 1

            # Remove trailing string length data
            data = data[:len(data) - len_count]

            # Then insert in the correct locations
            i = 0
            for L in self.string_locations:
                data.insert(L, strings[i])
                i += 1

            return data

        def process(self, bdata):
            self.callback(self.getData(bdata))


class Packer:

    def __init__(self, component):
        self.component = component
        self.pack_index = {}
        self.pack_list = []

        self.queued_data = []

    def registerRPC(self, key, callback, datatypes,
            reliable, replicate, private, server_only):

        dataprocessor = DataProcessor(self.component, callback, datatypes,
                reliable, replicate, private, server_only)

        existing = self.pack_index.get(key, None)

        if existing is None:
            self.pack_index[key] = len(self.pack_list)
            self.pack_list.append(dataprocessor)
        else:
            # Already exists... overwrite and throw warning
            self.pack_list[existing] = dataprocessor
            if key != '_attributes':
                print ("WARNING - RPC dataprocessor overwritten")

    def pack(self, key, data):
        p_id = self.pack_index[key]
        dataprocessor = self.pack_list[p_id]

        # Will be pulled by the component manager
        qdata = dataprocessor.getBytes(p_id, data)
        self.queued_data.append([dataprocessor,
                                qdata])

    def getDataProcessor(self, p_id):
        return self.pack_list[p_id]
