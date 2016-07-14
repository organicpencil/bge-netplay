from . import packer, component


def define():
    tdef = packer.TableDef('_add_object')
    tdef.define('uint16', 'id')
    tdef.define('float', 'x', 0.0)
    tdef.define('float', 'y', 0.0)
    tdef.define('float', 'z', 0.0)
    tdef.define('float', 'rot_x', 0.0)
    tdef.define('float', 'rot_y', 0.0)
    tdef.define('float', 'rot_z', 0.0)
    # Netplay needs a component reference on tables used to spawn components
    tdef.component = component.NetComponent
    # If you want to re-use a table for multiple components, the best option
    # is to create a new table with the old table as a template
    # new_tabledef = packer.TableDef('unique_name', template=old_tabledef)

    # Alternatively you can run them from an existing component and specify
    # component/whatever in the data.  But that will use more bandwidth