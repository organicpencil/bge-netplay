from . import packer


def define():
    tabledef = packer.TableDef('_permission')
    tabledef.define('uint16', 'id')
    tabledef.define('uint8', 'state')

    tabledef = packer.TableDef('_destroy')
    tabledef.define('uint16', 'id')

    tabledef = packer.TableDef('_GameObject')
    tabledef.define('uint16', 'id')
    tabledef.define('float', 'pos_x')
    tabledef.define('float', 'pos_y')
    tabledef.define('float', 'pos_z')
    tabledef.define('float', 'rot_x')
    tabledef.define('float', 'rot_y')
    tabledef.define('float', 'rot_z')
    tabledef.define('float', 'rot_w')

    tabledef = packer.TableDef('_RigidGameObject', template=tabledef)
    tabledef.define('float', 'lv_x')
    tabledef.define('float', 'lv_y')
    tabledef.define('float', 'lv_z')
    tabledef.define('float', 'av_x')
    tabledef.define('float', 'av_y')
    tabledef.define('float', 'av_z')