from serial import Serial
from time import sleep
from binascii import hexlify, unhexlify

''' TODO
* Make listFilesystem print all subdirs recursively, listing only files with full paths by default, starting from the given path. Empty paths defacto default to "/" so no extra logic needed. Optional Parameters list only files, dirs, or both in cwd. Remove duplicates and rename to list()
'''

class MPYSync:
    timeout = None
    FILE = 32768
    DIRECTORY = 16384

    def __init__(self, serial=None,port=None, baudrate = 115200) -> None:
        self.port = port
        self.baudrate = baudrate
        self.serial=serial
    
    def open(self):
        self.serial = Serial(self.port, timeout=self.timeout, baudrate = self.baudrate)
        print("rts:",self.serial.rts,",dtr:",self.serial.dtr)
        self.serial.rts=False
        self.serial.dtr=False
        self.flush()
    
    def close(self):
        if self.serial:
            self.serial.close()
            self.serial=None
    
    def flush(self,toPrint=False):
        # The following sequence is necessary, else atleast esp32s2 won't work right
        #self.command("",toPrint)
        #self.command("\x03",toPrint)
        #sleep(0.5)
        #self.command("")
        #sleep(0.01)
        #self.command("",toPrint)
        sleep(0.1)
        self.command("import os",toPrint)
        sleep(0.1)
        self.chdir("/",toPrint)
        sleep(0.01)
    
    def response(self, toPrint= False):
        end = False
        timedout = False
        terminator = ""
        message = ""
        while not end:
            result = self.serial.read().decode("utf-8")
            if result == "":
                if toPrint:
                    print(message)
                    print("TIMEOUT")
                timedout = True
                return message, timedout
            else:
                if result == ">" or result == " ":
                    terminator += result
                    if terminator == ">>> ":
                        end = True
                        message += terminator
                else:
                    if terminator != "":
                        message += terminator
                        terminator = ""
                    message += result
        
        if toPrint:
            print(message, end="")
        return message, timedout
    
    def command(self, string, toPrint=False, response=True):
        #self.serial.flushOutput()
        self.serial.write((string + "\r\n").encode("utf-8"))
        #self.serial.flushInput()
        if response:
            result = self.response(toPrint)
            message = []
            if not result[1]:
                message.append(result[0][len(string)+2:-6])
                message.append(False)
                return message
            else:
                print("")
                return result
    
    def listFilesystem(self, toPrint = False):
        response = self.command("os.listdir()", toPrint)[0]
        response = response.strip()
        response = response.lstrip("[")
        response = response.rstrip("]")
        files = response.split(", ")
        for i, file in enumerate(files):
            files[i] = files[i].lstrip("'")
            files[i] = files[i].rstrip("'")
            if toPrint:
                print(files[i])
        return files
    
    def listFilesDirectories(self, toPrint = False):
        self.command("for file in os.ilistdir():", toPrint, response=False)
        response = self.command("file\r\n\r\n\r\n", toPrint)[0]
        response = response.split("\r\n")
        #print(response)
        while not response[0].startswith("..."):
            del response[0]
        while response[0].startswith("..."):
            del response[0]
        files = []
        directories = []

        #print(response)
        for i, item in enumerate(response):
            if response[i] == "":
                del response[i]
        #response = response.rstrip(", ''")
        #response = response.lstrip('"')
        #response = response.rstrip('"')
        for item in response:
            item = item.lstrip("(")
            item = item.rstrip(")")
            item = item.split(", ")
            if item[1] == "16384":
                directories.append(item[0].strip("'"))
            else:
                files.append(item[0].strip("'"))
        
        return files, directories

    def removeFile(self, name, toPrint = False):
        files = self.listFiles()
        if name in files:
            self.command("os.remove('" + name + "')", toPrint)
    
    def remove(self, name):
        print("NOT IMPLEMENTED")
        self.command("import os")

    def mkdir(self, name):
        self.command("os.mkdir('" + name + "')")

    def rename(self, old, new):
        self.command("os.rename('" + old + "','" + new + "')")

    def getCWD(self, toPrint = False):
        result = self.command("os.getcwd()", toPrint)[0]
        result = result.strip()
        return result.strip("'")

    def chdir(self, name, toPrint = False):
        self.command("os.chdir('" + name + "')", toPrint)
    
    def fileInfo(self, name, toPrint = False):
        result = self.command("os.stat('" + name + "')")[0]
        result = result.lstrip("(")
        result = result.rstrip(")")
        result = result.split(", ")
        if int(result[0]) == self.DIRECTORY:
            return ["DIR", int(result[6])]
        else:
            return ["FILE", int(result[6])]
    
    def fileType(self, name, toPrint = False):
        return self.fileInfo(name, toPrint)[0]
    
    def fileSize(self, name, toPrint = False):
        return self.fileInfo(name, toPrint)[1]
    
    def getPath(self, name, asString = True, toPrint = False):
        path = name.split("/")
        path = path[0:-1]
        if asString:
            return "/".join(path)
        else:
            return path
    
    def getFileName(self, name, toPrint = False):
        return name.split("/")[-1]

    def ensurePath(self, name, purePath = True, toPrint = False):
        if not purePath:
            dirs = self.getPath(name, asString = False)
        else:
            dirs = [name]
        self.chdir("/")
        for dir in dirs:
            self.mkdir(dir)
            self.chdir(dir)

    def uploadFile(self, name, data):
        path = self.getPath(name, asString = True)
        self.ensurePath(path)
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.command("from binascii import unhexlify")
        self.command("f = open('" + name + "', 'w+')")
        self.command("f.write(unhexlify('" + hexlify(data).decode("utf-8") + "'))")
        self.command("f.close()")
        response = self.readFile(name)
        if response == data:
            return True
        else:
            print("VERIFICATION FAILED")
            return False

    def readFile(self, name):        
        self.command("from binascii import unhexlify", True)
        self.command("f = open('" + name + "', 'r')", True)
        response = self.command("print(hexlify(f.read()))", True)[0]
        response = response[2:-1]
        return unhexlify(response)