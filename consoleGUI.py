#! /usr/bin/python

from socket import socket,SHUT_RDWR,AF_INET,SOCK_DGRAM,SOCK_STREAM,SOL_SOCKET,TCP_NODELAY,IPPROTO_TCP,SO_REUSEADDR,SO_RCVBUF,SO_SNDBUF,timeout as SocketTimeout
from serial import Serial
from time import ctime,sleep,time
import tkinter as tk
import os,sys,re,pyperclip
from synchronizer import Synchronizer

class ConsoleGUI(tk.PanedWindow):
    bgColorEN = "gray12"
    fgColorEN = "white"
    fgColorD = "black"
    bgColorD = "gray"

    enumBootmode = 0
    enumBaudrate = 1
    enumPing = 2

    def __init__(self, master=None, port="127.0.0.1:4001", baudrate=115200, timeoutSerial=1,timeoutSocket=2):
        self.alpha = 0.9
        self.alphaEN = False
        self.buffer = b""
        self.cursor = 0
        self.sockBufSize=100

        if not master:
            master = tk.Tk()
        
        self.timeoutSerial = timeoutSerial
        self.timeoutSocket = timeoutSocket
        self.address=self.serial=self.tcp=self.udp=self.type=None

        self.stringVarPort = tk.StringVar()
        self.stringVarPort.set(port)

        if isinstance(master, tk.Tk):
            master.title(port)
        
        super().__init__(master=master)
        super().pack(fill=tk.BOTH,expand=True)
        self.pack(fill=tk.BOTH, expand=True)
        if self.alphaEN:
            self.master.bind("<Button-4>", self.onMouseWheel)
            self.master.bind("<Button-5>", self.onMouseWheel)
            try:
                self.wait_visibility(self.master)
                self.master.attributes("-alpha", self.alpha)
            except Exception as e:
                print("__init__():", type(e), e.args)
        5
        #self.master.attributes('-topmost', True)
        #self.master.update()
        
        self.controlsFrame = tk.PanedWindow(master=self)
        self.controlsFrame.pack(fill=tk.BOTH,expand=False)

        self.buttonClearscreen = tk.Button(self.controlsFrame, text="clear", command=self.onClearscreen)
        self.buttonClearscreen.pack(side=tk.LEFT)

        self.intVarTimestamps = tk.IntVar()
        self.intVarTimestamps.set(0)
        self.checkTimestamps = tk.Checkbutton(self.controlsFrame, text = "Timestamps", variable=self.intVarTimestamps)
        self.checkTimestamps.pack(side=tk.LEFT)

        self.intVarShowCR = tk.IntVar()
        self.intVarShowCR.set(0)
        self.checkShowCR = tk.Checkbutton(self.controlsFrame, text = "CR", variable=self.intVarShowCR)
        self.checkShowCR.pack(side=tk.LEFT)

        self.intVarTranslateCR = tk.IntVar()
        self.intVarTranslateCR.set(0)
        self.checkTranslateCR = tk.Checkbutton(self.controlsFrame, text = "CR->LF", variable=self.intVarTranslateCR)
        self.checkTranslateCR.pack(side=tk.LEFT)

        self.intVarRepr = tk.IntVar(value=0)
        self.checkRepr = tk.Checkbutton(self.controlsFrame, text = "Repr", variable=self.intVarRepr)
        self.checkRepr.pack(side=tk.LEFT)

        self.intVarRts = tk.IntVar(value=0)
        self.checkRts = tk.Checkbutton(self.controlsFrame, text = "RTS", variable=self.intVarRts, command=self.onRtsDtr)
        self.checkRts.pack(side=tk.LEFT)

        self.intVarDtr = tk.IntVar(value=0)
        self.checkDtr = tk.Checkbutton(self.controlsFrame, text = "DTR", variable=self.intVarDtr, command=self.onRtsDtr)
        self.checkDtr.pack(side=tk.LEFT)

        self.intVarAutoscroll = tk.IntVar(value=1)
        self.checkAutoscroll = tk.Checkbutton(self.controlsFrame, text = "Autoscroll", variable=self.intVarAutoscroll)
        self.checkAutoscroll.pack(side=tk.RIGHT)

        self.entryPort = tk.Entry(master=self.controlsFrame, textvariable=self.stringVarPort, width=16)
        self.entryPort.pack(side=tk.RIGHT, expand=False)
        self.entryPort.bind("<Return>", self.onPortEntry)

        self.intVarAttach = tk.IntVar(value=1)
        self.checkAttach = tk.Checkbutton(self.controlsFrame, text = "Attach", variable=self.intVarAttach, command=self.onAttach)
        self.checkAttach.pack(side=tk.RIGHT)

        self.stringVarBaud = tk.StringVar(master=self.controlsFrame, value="115200")
        self.entryBaud = tk.Entry(master=self.controlsFrame, textvariable=self.stringVarBaud, width=9)
        self.entryBaud.pack(side=tk.RIGHT, expand=False)
        self.entryBaud.bind("<Return>", self.onBaudEntry)

        self.controls2Frame = tk.PanedWindow(master=self)
        self.controls2Frame.pack(fill=tk.BOTH,expand=False)

        self.intVarEscape = tk.IntVar()
        self.intVarEscape.set(0)
        self.checkEscape = tk.Checkbutton(self.controls2Frame, text = "^[", variable=self.intVarEscape)
        self.checkEscape.pack(side=tk.LEFT)

        self.stringVarLength=tk.StringVar(value=500)
        self.entryLength = tk.Entry(master=self.controls2Frame,textvariable=self.stringVarLength,width=6)
        self.entryLength.pack(side=tk.RIGHT)

        self.labelLength=tk.Label(master=self.controls2Frame,text="Col Lim")
        self.labelLength.pack(side=tk.RIGHT)

        self.boolVarCapture=tk.BooleanVar(value=True)
        self.checkCapture = tk.Checkbutton(master=self.controls2Frame, text="Capture",variable=self.boolVarCapture,command=self.onCapture)
        self.checkCapture.pack(side=tk.LEFT)

        self.textFrame = tk.PanedWindow(master=self)
        self.textFrame.pack(fill=tk.BOTH,expand=True)
        
        self.textScrollbar = tk.Scrollbar(self.textFrame)
        self.textScrollbar.pack(side=tk.RIGHT, fill=tk.Y)        
        
        self.text = tk.Text(self.textFrame, width=1, height=1, foreground=self.fgColorEN, background=self.bgColorEN)
        self.text.pack(fill=tk.BOTH,expand=True)
        self.text.config(yscrollcommand=self.textScrollbar.set)
        self.text.bind("<Key>", self.onTextKeyboard)
        self.text.bind("<Button-3>", self.onRightClick)

        self.menu = tk.Menu(master=self.text,tearoff=0)
        self.menu.add_command(label="Copy",command=self.onCopy)
        self.menu.add_command(label="Paste",command=self.onPaste)
        #self.master.config(menu=self.menu)
        
        self.textScrollbar.config(command=self.text.yview)

        self.entryFrame = tk.PanedWindow(master=self)
        self.entryFrame.pack(fill=tk.X,expand=False)

        self.intVarEcho = tk.IntVar(value=0)
        self.checkEcho = tk.Checkbutton(self.entryFrame, text = "Echo", variable=self.intVarEcho)
        self.checkEcho.pack(side=tk.RIGHT)

        self.intVarEntryCR = tk.IntVar(value=0)
        self.checkEntryCR = tk.Checkbutton(self.entryFrame, text = "CR", variable=self.intVarEntryCR)
        self.checkEntryCR.pack(side=tk.RIGHT)

        self.intVarEntryLF = tk.IntVar(value=0)
        self.checkEntryLF = tk.Checkbutton(self.entryFrame, text = "LF", variable=self.intVarEntryLF)
        self.checkEntryLF.pack(side=tk.RIGHT)
        
        self.stringVarEntry = tk.StringVar()
        self.entryCommand = tk.Entry(master=self.entryFrame, textvariable=self.stringVarEntry, foreground=self.fgColorEN, background=self.bgColorEN)
        self.entryCommand.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entryCommand.bind("<Return>", self.onCommandEntry)

        if isinstance(self.master, tk.Tk):
            self.master.geometry("850x550")

        #self.close()
        self.onPortEntry()
        self.textAfter()

    def start(self):
        try:
            result=None
            if self.type == "serial":
                result = self.startSerial()
            elif self.type == "socket":
                result = self.startSocket()
            elif self.type: raise Exception("ConsoleGUI.start(): Unknown Port Type:",self.type)
            if result:
                self.text.configure(state='normal', foreground=self.fgColorEN, background=self.bgColorEN)
                self.entryCommand.configure(state='normal', foreground=self.fgColorEN, background=self.bgColorEN)
            else: self.close()
        except Exception as e:
            print("consoleGUI.start():",type(e), e.args)
            self.close()
    
    def startSocket(self):
        try:
            self.udp = socket(AF_INET, SOCK_DGRAM)
            self.udp.connect(self.address)
            self.tcp = socket(AF_INET, SOCK_STREAM)
            self.tcp.setsockopt(SOL_SOCKET,SO_REUSEADDR, 2)
            self.tcp.settimeout(self.timeoutSocket)
            self.tcp.connect(self.address)
            print(f"Connected to {self.address}")
            self.tcp.settimeout(0)
            self.tcp.setsockopt(IPPROTO_TCP,TCP_NODELAY,1)
            self.tcp.setsockopt(SOL_SOCKET,SO_RCVBUF,self.sockBufSize)
            self.tcp.setsockopt(SOL_SOCKET,SO_SNDBUF,self.sockBufSize)
            return True
        except SocketTimeout as e:
            print(f"Connection timeout -- {ctime()}")
        except ConnectionRefusedError:
            print(f"Connection refused -- {ctime()}")
        except Exception as e:
            print(f"ConsoleGUI.startSocket(): {type(e)}, {e.args} -- SocketMedium Closed -- {ctime()}")
        self.close()
        return False
    
    def startSerial(self):
        try:
            self.serial = Serial(port = self.stringVarPort.get(), timeout=self.timeoutSerial, baudrate = int(self.stringVarBaud.get()))
            self.serial.setDTR(self.intVarDtr.get())
            self.serial.setRTS(self.intVarRts.get())
            return True
        except Exception as e:
            print("startSerial():",type(e),len(e.args), e.args)
            self.close()
        return False
            
    def close(self):
        try:
            self.text.configure(state='disabled', foreground=self.fgColorD, background=self.bgColorD)
            self.entryCommand.configure(state='disabled', foreground=self.fgColorD, background=self.bgColorD)
            #self.intVarAttach.set(0)
            if self.type:
                if self.type=="serial":
                    if self.serial:
                        self.serial.close()
                        self.serial = None
                elif self.type=="socket":
                    try: self.tcp.shutdown(SHUT_RDWR)
                    except: pass
                    try: self.tcp.close()
                    except: pass
                    try: self.udp.close()
                    except: pass
                    self.tcp=self.udp=None
                else: raise Exception("ConsoleGUI.close(): Unknown Port Type:",self.type)
        except OSError as e:
            if e.errno == 107: pass
            else: print("ConsoleGUI.close():",type(e),e.args)
        except Exception as e:
            print("ConsoleGUI.close():",type(e),e.args)
    
    def onPortEntry(self, arg1=None,arg2=None,arg3=None):
        try:
            if self.stringVarPort.get():
                hostname=self.stringVarPort.get()
                for _hostname in ("localhost","0.0.0.0"):
                    hostname=hostname.replace(_hostname,"127.0.0.1")
                match = re.search("(\d+\.\d+\.\d+\.\d+)",hostname)
                if match:
                    self.type="socket"
                    address = hostname.split(":")
                    self.address=(address[0],int(address[1]))
                else:
                    self.type="serial"
                try:
                    if hostname: self.master.title(hostname)
                    else: self.master.title(self.stringVarPort.get())
                except Exception as e:
                    pass
                self.onAttach()
        except Exception as e:
            print("ConsoleGUI.onPortEntry():",type(e),e.args)
            self.close()
    
    def onAttach(self):
        try:
            if self.intVarAttach.get():
                self.start()
                self.onRtsDtr()
                self.onBaudEntry(None)
            else: self.close()
        except OSError as e: self.close()
        except Exception as e:
            print("ConsoleGUI.onAttach():", type(e),e.args)
            self.close()

    def onClearscreen(self):
        _state=self.text.config("state")[4]
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state=_state)

    def onEsptool(self):
        print("onEsptool")
   
    def serialRead(self):
        try:
            if self.serial:
                inwaiting = self.serial.in_waiting
                bytes = self.serial.read(inwaiting)
                if len(bytes) < inwaiting:
                    raise Exception("bytes < self.serial.in_waiting")
                if bytes: self.processText(self.buffer + bytes)
        except OSError as e:
            if e.errno==5:pass
            else: print("ConsoleGUI.serialRead():", type(e), e.args)
            self.close()
        except Exception as e:
            print("ConsoleGUI.serialRead():", type(e), e.args)
            self.close()
            return
    
    def socketRead(self):
        try:
            if self.tcp:
                try:
                    blockingError=False
                    bytes = self.tcp.recv(100)
                    #print("rcvbuf:",self.tcp.getsockopt(SOL_SOCKET,SO_RCVBUF),",sndbuf:",self.tcp.getsockopt(SOL_SOCKET,SO_SNDBUF))
                except BlockingIOError as e:
                    bytes=b""
                    blockingError = True
                    if e.errno==11 or e.errno==10035: pass
                    else: print("ConsoleGUI.socketRead():",type(e),e.args)
                if not blockingError and not bytes: self.close()
                if bytes: self.processText(self.buffer + bytes)
        except ConnectionResetError: self.close()
        except Exception as e:
            print("consoleGUI.socketRead():", type(e), e.args)
    
    def processText(self, bytes = b""):
        try:
            #print(f"\n\nIteration {self.i}","\nLast Line:",self.text.get(f'{self.text.index("end-1c").split(".")[0]}.0',tk.END))
            if self.intVarEscape.get() and not self.intVarRepr.get():
                pattern = b"([\b])|([\x1b])"
                while match := re.search(pattern, bytes):
                    #print("")
                    #print("buffer:",self.buffer,"bytes:",bytes," ----------- ","match:",match.group())
                    if  match.group(1):
                        self._processText(bytes[:match.start()])
                        self.text.delete(tk.END + "-2c")
                        bytes = bytes[match.end():]
                    elif match.group(2):
                        self._processText(bytes[:match.start()])
                        bytes = bytes[match.start():]
                        _pattern = b"\x1b\[([\x30-\x3F]*)[\x20-\x2F]*([\x40-\x7E])"
                        if match := re.search(_pattern, bytes):
                            #print("Bytes:",bytes," -- ","match:",match.group())
                            if match.group(2) == b"D" and match.group(1).isdigit():
                                self.cursor += int(match.group(1))
                                #print("Setting Cursor Position:",self.cursor)
                                #print("Last Line Now:",self.text.get(f'{self.text.index("end-1c").split(".")[0]}.0',tk.END))
                            elif match.group(2) == b"K":
                                #print(f"Deleting {self.cursor} chars")
                                if self.cursor>0:
                                    self.text.delete(f"end-{1+self.cursor}c","end")
                                    self.cursor=0
                                #print("Last Line Now:",self.text.get(f'{self.text.index("end-1c").split(".")[0]}.0',tk.END))
                            else:
                                raise Exception("Unknown Escape Sequence")
                            bytes = bytes[match.end():]
                        else:
                            self.buffer=bytes
                            #print("Incomplete Escape Sequence")
                            return
                self.buffer=b""
            self._processText(bytes)
            #print("Last Line:",self.text.get(f'{self.text.index("end-1c").split(".")[0]}.0',tk.END))
        except Exception as e:
            print("ConsoleGUI._processText():",type(e),e.args)
    
    def _processText(self, bytes = b""):
        if bytes:
            if self.intVarTranslateCR.get():
                bytes = bytes.replace(b"\r", b"\n")
            if not self.intVarShowCR.get():
                bytes = bytes.replace(b"\r", b" ")
            bytesList = bytes.split(b"\n")
            for x, bytes in enumerate(bytesList):
                if self.intVarRepr.get() and len(bytesList[x]) > 0:
                        bytesList[x] = repr(bytesList[x]).encode("utf-8")[2:-1]
                if self.intVarTimestamps.get() and x>0:
                    bytesList[x] = f"<{ctime().split()[3]}:{round(time()%1*1000)%1000:03d}".encode("utf-8")+">\t".encode("utf-8") + bytesList[x]
            if self.cursor>0:
                #print(f"Overwriting {self.cursor} chars.")
                self.text.delete(f"end-{1+self.cursor}c", "end")
                self.cursor=0
            else:
                count=0
                for bytes in bytesList:
                    count+=len(bytes)
                #print(f"Writing {count} chars.")
            
            lineLengthLimit=int(self.stringVarLength.get())
            for x,line in enumerate(bytesList):
                #print("line length:",self.text.index(tk.END+"-1c").split(".")[1])
                diff=lineLengthLimit-int(self.text.index(tk.END+"-1c").split(".")[1])
                while len(line)>diff:
                    self.text.insert(tk.END, line[0:diff]+b"\n")
                    line=line[diff:]
                    diff=lineLengthLimit-int(self.text.index(tk.END+"-1c").split(".")[1])
                self.text.insert(tk.END, line[0:diff])
                if x<len(bytesList)-1:
                    self.text.insert(tk.END, "\n")
            if self.intVarAutoscroll.get():
                self.text.see(tk.END)
            #print("Last Line:", self.text.get(f'{self.text.index("end-1c").split(".")[0]}.0',tk.END))
    
    def textAfter(self):
        try:
            self.text.after(10, self.textAfter)
            if self.type=="serial":
                self.serialRead()
            elif self.type=="socket":
                self.socketRead()
            #elif self.type:
            #    raise Exception("consoleGUI.textAfter(): Unknown Type")
        except Exception as e:
            print("ConsoleGUI.textAfter():",type(e),e.args)

    def onRtsDtr(self):
        try:
            if self.type=="serial":
                self.serial.setRTS(self.intVarRts.get())
                self.serial.setDTR(self.intVarDtr.get())
            elif self.type=="socket": self.udp.send(ConsoleGUI.enumBootmode.to_bytes(1,"big")+(not self.intVarRts.get()).to_bytes(1,"big")+(not self.intVarDtr.get()).to_bytes(1,"big"))
            print("ConsoleGUI.onRtsDtr:",int(not self.intVarRts.get()),int(not self.intVarDtr.get()))
        except AttributeError: pass
        except ConnectionRefusedError:
            if self.type=="socket": self.close()
        except Exception as e:
            print("onRtsDtr():", type(e), e.args)
            self.close()

    def onCommandEntry(self, arg):
        try:
            self.serial.write(self.stringVarEntry.get().encode("utf-8"))
            if self.intVarEcho.get():
                self.text.insert(tk.END, self.stringVarEntry.get())
            if self.intVarEntryCR.get():
                self.serial.write("\r".encode("utf-8"))
                if self.intVarEcho.get():
                    self.text.insert(tk.END, "\r")
            if self.intVarEntryLF.get():
                self.serial.write("\n".encode("utf-8"))
                if self.intVarEcho.get():
                    self.text.insert(tk.END, "\n")
            self.stringVarEntry.set("")
            self.text.see(tk.END)
        except Exception as e:
            print("onCommandEntry():", type(e), e.args)
    
    def onBaudEntry(self, arg):
        baudrate=int(self.stringVarBaud.get())
        try:
            if self.type=="serial":
                self.serial.baudrate = baudrate
            elif self.type=="socket":
                self.udp.send(ConsoleGUI.enumBaudrate.to_bytes(1,"big")+baudrate.to_bytes(4,"big"))
            print("ConsoleGUI.onBaudEntry():",baudrate)
        except AttributeError: pass
        except ConnectionRefusedError:
            if self.type=="socket": self.close()
        except Exception as e:
            print("onBaudEntry():", type(e), e.args)
            self.close()
    
    def onTextKeyboard(self, arg):
        if isinstance(arg,str):
            char=arg
            bytes = char.encode("utf-8")
        else:
            char=arg.char
            if arg.keycode == 111: # UP
                bytes = b"\x1B[A"
            elif arg.keycode == 116: # DOWN
                bytes = b"\x1B[B"
            elif arg.keycode == 113: # LEFT
                bytes = b"\x1B[D"
            elif arg.keycode == 114: #RIGHT
                bytes = b"\x1B[C"
            else:
                bytes = char.encode("utf-8")
        
        if self.intVarEcho.get():
            if self.intVarTranslateCR.get():
                char.replace("\r","\n")
            self._processText(char.encode("utf-8"))
        
        try:
            if self.type=="serial":
                self.serial.write(bytes)
            elif self.type=="socket":
                self.tcp.send(bytes)
        except BrokenPipeError:
            self.close()
        except Exception as e:
            print("ConsoleGUI.onTextKeyboard()",type(e),e.args)
        return "break"
    
    def onMouseWheel(self, arg):
        if arg.num == 4:
            self.alpha -= 0.05
            if self.alpha < 0.5:
                self.alpha = 0.5
        if arg.num == 5:
            self.alpha += 0.05
            if self.alpha > 1:
                self.alpha = 1
        if arg.num == 4 or arg.num == 5:
            try:
                self.master.attributes("-alpha", self.alpha)
            except:
                pass

    def onRightClick(self,arg):
        self.clickX=arg.x
        self.clickY=arg.y
        self.menu.tk_popup(arg.x_root, arg.y_root)
    
    def onCopy(self):
        #print("onCopy",self.clickX,self.clickY)
        pyperclip.copy(self.text.selection_get())
    
    def onPaste(self):
        #self.text.insert("end",pyperclip.paste())
        #print("onPaste",self.clickX,self.clickY)
        self.onTextKeyboard(pyperclip.paste())

    def onCapture(self):
        if self.boolVarCapture.get():
            print("bind")
            self.text.bind("<Key>", self.onTextKeyboard)
        else:
            print("Unbind")
            self.text.unbind("<Key>")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ConsoleGUI(port=sys.argv[1]).mainloop()
    else:
        ConsoleGUI().mainloop()
