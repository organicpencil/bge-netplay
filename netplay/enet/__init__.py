import platform

system = platform.system()
arch = platform.architecture()[0]

USE_ENET = True
if system == 'Linux':
    if arch == '32bit':
        from .linux32 import enet
    elif arch == '64bit':
        from .linux64 import enet
    else:
        USE_ENET = False
        print ("Unsupported architecture %s - expected 32bit or 64bit" % (arch))

elif system == 'Windows':
    if arch == '32bit':
        from .windows32 import enet
    elif arch == '64bit':
        #from .windows64 import enet
        USE_ENET = False
        print ("32 bit blender is required for multiplayer on Windows")
    else:
        USE_ENET = False
        print ("Unsupported architecture %s - expected 32bit or 64bit" % (arch))

else:
    try:
        from . import enet
    except:
        USE_ENET = False
        print ("Enet was not supplied for %s" % (system))
        print ("But you can go to https://github.com/aresch/pyenet and build it yourself")
        
        
if not USE_ENET:
    enet = None
