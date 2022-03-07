import winreg, ctypes, os, sys
from subprocess import list2cmdline

def isAdmin():
    admin = False
    try:
        admin = (os.getuid() == 0)
    except AttributeError:
        admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return admin

def admin():
    if isAdmin():
        print("Already administrator!")
    else:
        print("Running as administrator...")
        #args = []
        #for arg in sys.argv:
        #    if arg.find(" ") != -1:
        #        arg = f'"{arg}"'
        #    args.append(arg)
        #ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(args), None, 1)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, list2cmdline(sys.argv), None, 1)
        exit()

typeinfo = {
    winreg.REG_BINARY: ("BINARY", "Binary data, in any form."),
    winreg.REG_DWORD: ("DWORD", "A 32-bit number."),
    #winreg.REG_DWORD_LITTLE_ENDIAN: ("DWORD (Little Endian)", "A 32-bit number in little-endian format. Equivalent to DWORD.", "DWORD_LITTLE_ENDIAN"),
    winreg.REG_DWORD_BIG_ENDIAN: ("DWORD (Big Endian)", "A 32-bit number in big-endian format.", "DWORD_BIG_ENDIAN"),
    winreg.REG_QWORD: ("QWORD", "A 64-bit number."),
    #winreg.REG_QWORD_LITTLE_ENDIAN: ("QWORD (Little Endian)", "A 64-bit number in little-endian format. Equivalent to QWORD.", "QWORD_LITTLE_ENDIAN"),
    winreg.REG_RESOURCE_LIST: ("RESOURCE_LIST", "A device-driver resource list."),
    winreg.REG_FULL_RESOURCE_DESCRIPTOR: ("FULL_RESOURCE_DESCRIPTOR", "A hardware setting."),
    winreg.REG_RESOURCE_REQUIREMENTS_LIST: ("RESOURCE_REQUIREMENTS_LIST", "A hardware resource list."),
    winreg.REG_SZ: ("STRING", "A null-terminated string."),
    winreg.REG_EXPAND_SZ: ("STRING (Expand)", "Null-terminated string containing references to environment variables (%PATH%).", "STRING_EXPAND"),
    winreg.REG_MULTI_SZ: ("STRING (Multi)", "A sequence of null-terminated strings, terminated by two null characters.", "STRING_MULTI"),
    winreg.REG_LINK: ("LINK", "A Unicode symbolic link."),
    winreg.REG_NONE: ("NONE", "No defined value type.")
}

registries = {
    winreg.HKEY_CLASSES_ROOT: ("HKEY_CLASSES_ROOT", "Registry entries subordinate to this key define types (or classes) of documents and the properties associated with those types. Shell and COM applications use the information stored under this key."),
    winreg.HKEY_CURRENT_USER: ("HKEY_CURRENT_USER", "Registry entries subordinate to this key define the preferences of the current user. These preferences include the settings of environment variables, data about program groups, colors, printers, network connections, and application preferences."),
    winreg.HKEY_LOCAL_MACHINE: ("HKEY_LOCAL_MACHINE", "Registry entries subordinate to this key define the physical state of the computer, including data about the bus type, system memory, and installed hardware and software."),
    winreg.HKEY_USERS: ("HKEY_USERS", "Registry entries subordinate to this key define the default user configuration for new users on the local computer and the user configuration for the current user."),
    winreg.HKEY_PERFORMANCE_DATA: ("HKEY_PERFORMANCE_DATA", "Registry entries subordinate to this key allow you to access performance data. The data is not actually stored in the registry; the registry functions cause the system to collect the data from its source."),
    winreg.HKEY_CURRENT_CONFIG: ("HKEY_CURRENT_CONFIG", "Contains information about the current hardware profile of the local computer system.")
}

def typeHelp(type):
    """Get the description of a value type."""
    t = typeinfo[type]
    print(f"{t[0]}: {t[1]}")
    
def registryHelp(type):
    """Get the description of a registry."""
    t = registries[type]
    print(f"{t[0]}: {t[1]}")

def getValueName(type):
    """Returns the name to display for this type."""
    return typeinfo[type][2]

typelist = []

for t in typeinfo.items():
    typ = t[0]
    i = t[1]
    if len(i) >= 3:
        stored_name = i[2]
    else:
        stored_name = i[0]
        typeinfo[typ] = typeinfo[typ] + tuple([stored_name])
    typelist.append(stored_name)
    globals()[stored_name] = typ

registrylist = []

for r in registries.items():
    typ = r[0]
    i = r[1]
    name = i[0]
    registrylist.append(name)
    globals()[name] = typ

access = winreg.KEY_READ | winreg.KEY_SET_VALUE

registry = winreg.ConnectRegistry(None, HKEY_CURRENT_USER)

registryName = registries[HKEY_CURRENT_USER][0]

stack = []

currentName = None

current = registry

def changeRegistry(reg):
    global registry, registryName, stack, currentName, current
    oldReg = registry
    
    registry = winreg.ConnectRegistry(None, reg)
    registryName = registries[reg][0]
    stack = []
    currentName = None
    current = registry
    
    oldReg.Close()

def format(id, val):
    value = str(val)
    if id == STRING or id == STRING_EXPAND or id == STRING_MULTI or id == LINK:
        value = f'"{value}"'
    return value

def list():
    global current
    i = 0
    while True:
        try:
            key = winreg.EnumKey(current, i)
            string = str(key)
            if key.isnumeric():
                string = f'"{key}"'
            else:
                if key.startswith('"'):
                    string = f'\\{string}'
                if key.endswith('"'):
                    string = f'{string[0:len(string)-1]}\\"'
            print(string)
            i = i + 1
        except EnvironmentError:
            break
    i = 0
    while True:
        try:
            key = winreg.EnumValue(current, i)
            id = key[2]
            value = format(id, key[1])
            
            # print(f'"{key[0]}": "{winreg.QueryValueEx(current, key[0])}"')
            print(f'{getValueName(id)} "{key[0]}": {value}')
            i = i + 1
        except EnvironmentError:
            break

def rawpath():
    return "\\".join(stack)

def path():
    return registryName + "\\" + rawpath()

def move(string):
    global current, stack, currentName, access
    old = current
    curr = string
    hasBackslash = string.find("\\") != -1
    if hasBackslash:
        curr = string[string.rfind("\\")+1::]
    currentName = curr
    prevLen = len(stack)
    if hasBackslash:
        stack.extend(string.split("\\"))
    else:
        stack.append(string)
    move_path = rawpath()
    try:
        current = winreg.OpenKey(registry, move_path, access=access)
    except OSError as e:
        if e.winerror == 5:
            globals()['current'] = winreg.OpenKey(registry, move_path)
            print("Key could not be opened with write access.")
        elif e.winerror == 2:
            stack = stack[:prevLen]
            raise e
        else:
            raise e
    if old != registry:
        old.Close()
    print(path())

def up():
    global currentName, stack, current, access
    currentName = stack.pop()
    if len(stack) > 0:
        up_path = rawpath()
        try:
            current = winreg.OpenKey(registry, up_path, access=access)
        except OSError as e:
            if e.winerror == 5:
                current = winreg.OpenKey(registry, up_path)
                print("Key could not be opened with write access.")
            else:
                raise e
    else:
        current = registry
    print(path())

def setValue(name, value):
    global current
    
    val = winreg.QueryValueEx(current, name)
    typ = val[1]
    
    winreg.SetValueEx(current, name, 0, typ, value)
    
def createOrSetValue(name, value, type):
    global current
    
    winreg.SetValueEx(current, name, 0, type, value)

cmds = [
#'Constants: ',
'There are constants for all of the value types',
'These are: ' + ", ".join(typelist),
'There are constants for all of the registry hives',
'These are: ' + ", ".join(registrylist),
'Default registry hive is HKEY_CURRENT_USER',
'Commands: ',
'"admin()": try to run this program with administrator privileges if it isn\'t already',
'"exit()": exit the python',
'"typeHelp(<type>)": Prints the description of the registry type',
'"registryHelp(<registry>)": Prints the description of the registry type',
'"changeRegistry(<registry>)": change to the respective registry hive',
'"list()": Lists the keys and values in the current location ()',
'          to prevent confusion, purely numeric keys will be surrounded in double quotes (")',
'"move(String <key>)": Move to the respecive key',
'"up()": Move up to the previous key',
'"setValue(String <valueName>, <value>)": Set the value with name [valueName] to [value]',
'"createOrSetValue(String <valueName>, <value>, <valueType>)": Set the value with name [valueName] to [value] with type [valueType], creates a value if it doesn\'t already exist'
]
print()
for c in cmds: print(c)
print()
print()
if not isAdmin():
    print("Python is not running as an administrator, you will probably")
    print("be restricted to only being able to write in HKEY_CURRENT_USER")
    print("You'll probably still be able to read everywhere else, though.")
    print("Call admin() to try and run as administrator")
    print()

print("More features are planned, and there may still be a few bugs :/")
print()

while True:
    code = input("Enter Command: ")
    print()
    try:
        ret = exec(code)
        if ret != None:
            print(ret)
    except Exception as e:
        print(e)
    print()
