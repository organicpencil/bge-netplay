from . import packer


def define():
    tabledef = packer.TableDef('_permission')
    tabledef.define('uint16', 'id')
    tabledef.define('uint8', 'state')

    tabledef = packer.TableDef('_destroy')
    tabledef.define('uint16', 'id')

    tabledef = packer.TableDef('_StaticSetup')
    tabledef.define('uint16', 'id')
    tabledef.define('float', 'pos_x')
    tabledef.define('float', 'pos_y')
    tabledef.define('float', 'pos_z')
    tabledef.define('float', 'rot_x')
    tabledef.define('float', 'rot_y')
    tabledef.define('float', 'rot_z')