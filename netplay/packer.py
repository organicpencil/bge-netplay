import collections
import copy
import json
import struct
import warnings


_DATA_TYPES = {}
_DATA_TYPES['float'] = 'f'
_DATA_TYPES['double'] = 'd'
_DATA_TYPES['int8'] = 'b'
_DATA_TYPES['uint8'] = 'B'
_DATA_TYPES['int16'] = 'h'
_DATA_TYPES['uint16'] = 'H'
_DATA_TYPES['int32'] = 'i'
_DATA_TYPES['uint32'] = 'I'
_DATA_TYPES['int64'] = 'q'
_DATA_TYPES['uin64'] = 'Q'
_DATA_TYPES['json'] = 'json'

_TABLES = {}
_TABLE_LIST = []


def join_buffers(bufflist):
    # Aggregates small buffers to reduce packet overhead
    # There is no length limit.  We expect fragmentation to be done elsewhere.
    buff = b''
    for b in bufflist:
        b = struct.pack('!H', len(b)) + b
        buff += b

    # Arranged size,data,size,data....
    return buff


def unjoin_buffers(buff):
    # Returns a list of buffers that can each be converted with to_table
    bufflist = []
    i = 0
    while i < len(buff):
        size = struct.unpack('!H', buff[:i + 2][i:])[0]
        bufflist.append(buff[:i + 2 + size][i + 2:])
        i = i + 2 + size

    return bufflist


def to_bytes(table):
    tabledef = table._tabledef
    data = []
    json_data = []

    for key, value in table._data.items():
        d = value[0]
        v = value[1]

        if v is None:
            raise KeyError("Missing required field: {}".format(key))

        if d == 'json':
            json_data.append([key, v])
        else:
            data.append(v)

    buff = struct.pack(tabledef._formatstring, tabledef._id, *data)
    if len(json_data):
        buff += bytes(json.dumps(json_data), 'UTF-8')

    return buff


def to_table(buff):
    # Read the first 2 bytes to determine table ID
    table_id = struct.unpack('!H', buff[:2])[0]
    try:
        tabledef = _TABLE_LIST[table_id]
    except IndexError as err:
        msg = 'Table ID {} missing'.format(table_id)
        err.args = err.args + (msg,)
        raise

    size = struct.calcsize(tabledef._formatstring)
    data = struct.unpack(tabledef._formatstring, buff[:size])

    table = Table(tabledef)

    i = 1  # table ID is still in here, so we skip
    for key, value in tabledef._datatypes.items():
        d = value[0]

        if d == 'json':
            # Check for json at the end
            continue
        else:
            v = data[i]
            table.set(key, v)

        i += 1

    if len(buff) > size:
        # There is json
        json_data = json.loads(bytes.decode(buff[size:], 'UTF-8'))
        for key, value in json_data:
            table.set(key, value)

    return table


class TableDef:
    def __init__(self, name, template=None):
        if _TABLES.get(name, None) is not None:
            warnings.warn("Table already defined: {}".format(name))

        self._name = name
        self._id = len(_TABLE_LIST)

        if template is None:
            self._datatypes = collections.OrderedDict()
            self._formatstring = '!H'
        else:
            self._datatypes = copy.deepcopy(template._datatypes)
            self._formatstring = template._formatstring

        _TABLES[name] = self
        _TABLE_LIST.append(self)

    def define(self, datatype, key, default=None):
        d = self._datatypes

        if d.get(key, None) is not None:
            warnings.warn("Key already defined: {}".format(key))

        if _DATA_TYPES.get(datatype, None) is None:
            raise KeyError("Invalid datatype: {}".format(datatype))

        d[key] = [_DATA_TYPES[datatype], default]
        self._datatypes = collections.OrderedDict(sorted(list(d.items()),
                key=lambda t: t[0]))

        # Rebuild the format string
        formatstring = '!H'

        for value in self._datatypes.values():
            d = value[0]
            if d != 'json':  # json is appened to the end of the buffer
                formatstring += d

        self._formatstring = formatstring

    def tableName(self):
        return self._name

    def tableID(self):
        return self._id


class Table:
    def __init__(self, tabledef):
        if type(tabledef) is str:
            # Fails if the table hasn't been defined
            tabledef = _TABLES[tabledef]

        self._data = copy.deepcopy(tabledef._datatypes)
        self._tabledef = tabledef  # For referencing ID and format string

    def set(self, key, value):
        try:
            self._data[key][1] = value
        except KeyError as err:
            msg = 'Did you forget to run TableDef.define?'.format(key)
            err.args = err.args + (msg,)
            raise

    def get(self, key):
        value = self._data.get(key, None)
        if value is not None:
            value = value[1]
        return value

    def tableName(self):
        return self._tabledef._name

    def tableID(self):
        return self._tabledef._id
