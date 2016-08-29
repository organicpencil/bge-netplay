from . import packer, component


def define():
    tabledef = packer.TableDef('_permission')
    tabledef.define('uint16', 'id')
    tabledef.define('uint8', 'state')