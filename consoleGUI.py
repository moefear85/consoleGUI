#! /usr/bin/python

from serial import Serial
import serial.serialutil
from time import sleep
from select import poll
from _thread import start_new_thread as start
import tkinter as tk
import tkinter.ttk as ttk
import sys, time, re

class state:
    normal = 0
    buffering = 1

class SerialFrame(tk.PanedWindow):
    bgColorEN = "gray12"
    fgColorEN = "white"
    fgColorD = "black"
    bgColorD = "gray"

    def __init__(self, master=None, port=None, baudrate=115200, timeout=1000):
        self.alpha = 0.9
        self.alphaEN = False
        self.state = state.normal
        self.buffer = b""
        self.cursor = 0

        if not master:
            master = tk.Tk()
        
        self.stringVarPort = tk.StringVar()
        self.fPort(port)
        self.baudrate = baudrate
        self.timeout = timeout

        if isinstance(master, tk.Tk):
            master.title(self.fPort(none=False))
        
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
        self.checkRts = tk.Checkbutton(self.controlsFrame, text = "RTS", variable=self.intVarRts, command=self.onRts)
        self.checkRts.pack(side=tk.LEFT)

        self.intVarDtr = tk.IntVar(value=0)
        self.checkDtr = tk.Checkbutton(self.controlsFrame, text = "DTR", variable=self.intVarDtr, command=self.onDtr)
        self.checkDtr.pack(side=tk.LEFT)

        self.intVarAutoscroll = tk.IntVar(value=1)
        self.checkAutoscroll = tk.Checkbutton(self.controlsFrame, text = "Autoscroll", variable=self.intVarAutoscroll)
        self.checkAutoscroll.pack(side=tk.RIGHT)

        self.entryPort = tk.Entry(master=self.controlsFrame, textvariable=self.stringVarPort, width=13)
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
        self.intVarEscape.set(1)
        self.checkEscape = tk.Checkbutton(self.controls2Frame, text = "^[", variable=self.intVarEscape)
        self.checkEscape.pack(side=tk.LEFT)

        self.textFrame = tk.PanedWindow(master=self)
        self.textFrame.pack(fill=tk.BOTH,expand=True)
        
        self.textScrollbar = tk.Scrollbar(self.textFrame)
        self.textScrollbar.pack(side=tk.RIGHT, fill=tk.Y)        
        
        self.text = tk.Text(self.textFrame, width=1, height=1, foreground=self.fgColorEN, background=self.bgColorEN)
        self.text.pack(fill=tk.BOTH,expand=True)
        self.text.config(yscrollcommand=self.textScrollbar.set)
        self.text.bind("<Key>", self.onTextKeyboard)
        
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
            self.master.geometry("800x550")
        
        self.onPortEntry(None)

        self.textAfter()
    
    def __enter__(self):
        self.serial = Serial(port = self.fPort(), timeout=self.timeout, baudrate = self.baudrate)
        return self
    
    def __exit__(self, type, value, traceback):
        self.serial.close()
        self.serial = None

    def startSerial(self):
        try:
            self.text.configure(state='normal', foreground=self.fgColorEN, background=self.bgColorEN)
            self.entryCommand.configure(state='normal', foreground=self.fgColorEN, background=self.bgColorEN)
            self.__enter__()
            self.serial.setDTR(self.intVarDtr.get())
            self.serial.setRTS(self.intVarRts.get())
            #start(self.serialLoop, ())
        except Exception as e:
            if isinstance(e, serial.serialutil.SerialException) and e.args[0] == 2:
                #print("Serial Closed")
                pass
            else:
                print("startSerial():",type(e),len(e.args), e.args)
                #self.configure(state='disable') Don't uncomment. Throws bogus TclError attempting to pass "state" to self.serial
                #self.textFrame.configure(state='disable') Don't uncomment. Same Reason
            self.text.configure(state='disable', foreground=self.fgColorD, background=self.bgColorD)
            self.entryCommand.configure(state='disable', foreground=self.fgColorD, background=self.bgColorD)
    
    def onPortEntry(self, arg):
        port = self.fPort()
        try: self.master.title(port)
        except Exception as e:
            print("onPortEntry():", type(e), e.args)
        self.onAttach()
    
    def onClearscreen(self):
        self.text.delete("1.0", "end")

    def onEsptool(self):
        print("onEsptool")

    def onAttach(self):
        if self.intVarAttach.get():
            self.startSerial()
        else:
            self.text.configure(state='disable', foreground=self.fgColorD, background=self.bgColorD)
            self.entryCommand.configure(state='disable', foreground=self.fgColorD, background=self.bgColorD)
            try:
                #print("Serial Closed")
                self.serial.close()
            except Exception as e:
                print("onAttach():", type(e), e.args)
            finally:
                self.serial = None
    
    def fPort(self, port = None, none=True):
        if port:
            self.stringVarPort.set(port)
            #self.onPortEntry(None)
        elif not none:
            return self.stringVarPort.get()
        elif self.stringVarPort.get() == "":
            return None
        else:
            return self.stringVarPort.get()
    
    def serialLoop(self):
        try:
            while True:
                #self.serial.in_waiting
                try:
                    byte = self.serial.read(1)
                except Exception as e:
                    print("serialLoop():", type(e), e.args)
                    return
                if byte == b"\r":
                    if not self.intVarShowCR.get():
                        byte = b''
                    elif self.intVarTranslateCR.get():
                        byte = b"\n"
                if self.intVarRepr.get():
                    byte = repr(byte)[2:-1]
                self.text.insert(tk.END, byte)
                if self.intVarAutoscroll.get():
                    self.text.see(tk.END)
        except Exception as e:
            print("serialLoop():",type(e), e.args)
    
    def serialIteration(self):
        try:
            inwaiting = self.serial.in_waiting
            bytes = self.serial.read(inwaiting)
            if len(bytes) < inwaiting:
                raise Exception("bytes < self.serial.in_waiting")
        except Exception as e:
            print("serialIteration():", type(e), e.args)
            return
        if self.buffer or bytes:
            self.processText(self.buffer + bytes)
    
    def processText(self, bytes = b""):
        if self.intVarEscape.get() and not self.intVarRepr.get():        
            pattern = b"([\b])|([\x1b])"
            while match := re.search(pattern, bytes):
                if  match.group(1):
                    self._processText(bytes[:match.start()])
                    self.text.delete(tk.END + "-2c")
                    bytes = bytes[match.end():]
                elif match.group(2):
                    self._processText(bytes[:match.start()])
                    bytes = bytes[match.start():]
                    pattern = b"\x1b\[([\x30-\x3F]*)[\x20-\x2F]*([\x40-\x7E])"
                    if match := re.search(pattern, bytes):
                        if match.group(2) == b"D" and match.group(1).isdigit():
                            self.cursor = int(match.group(1))
                        elif match.group(2) == b"K":
                            for x in range(self.cursor):
                                self.text.delete(tk.END + "-2c")
                        else:
                            raise("Unknown Escape Sequence")
                        bytes = bytes[match.end():]
                    else:
                        raise Exception("Incomplete Escape Sequence")
        self._processText(bytes)
    
    def _processText(self, bytes = b""):
        if self.intVarTranslateCR.get():
            bytes = bytes.replace(b"\r", b"\n")
        if not self.intVarShowCR.get():
            bytes = bytes.replace(b"\r", b"")
        bytesList = bytes.split(b"\n")
        for x, bytes in enumerate(bytesList):
            if self.intVarRepr.get() and len(bytesList[x]) > 0:
                    bytesList[x] = repr(bytesList[x]).encode("utf-8")[2:-1]
            if self.intVarTimestamps.get() and x>0:
                bytesList[x] = f"<{time.ctime().split()[3]}:{round(time.time()%1*1000):3d}".encode("utf-8")+">\t".encode("utf-8") + bytesList[x]
        while self.cursor > 0:
            self.text.delete(tk.END + "-2c")
            self.cursor -=1
        self.text.insert(tk.END, b"\n".join(bytesList))
        if self.intVarAutoscroll.get():
            self.text.see(tk.END)
    
    def textAfter(self):
        self.text.after(10, self.textAfter)
        if self.serial and self.serial.isOpen():
            self.serialIteration()

    def onRts(self):
        try: self.serial.setRTS(self.intVarRts.get())
        except Exception as e:
            print("onRts():", type(e), e.args)
    
    def onDtr(self):
        try: self.serial.setDTR(self.intVarDtr.get())
        except Exception as e:
            print("onDtr():", type(e), e.args)

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
        self.baudrate=int(self.stringVarBaud.get())
        print(self.baudrate)
        try:
            self.serial.baudrate = self.baudrate
        except Exception as e:
            print("onBaudEntry():", type(e), e.args)
    
    def onTextKeyboard(self, arg):
        #print(arg)
        if self.intVarEcho.get():
            if arg.char == "\r" and self.intVarTranslateCR.get():
                arg.char = "\n"
            self.text.insert(tk.END, arg.char)
            self.text.see(tk.END)
        if arg.keycode == 111: # UP
            bytes = b"\x1B[A"
        elif arg.keycode == 116: # DOWN
            bytes = b"\x1B[B"
        elif arg.keycode == 113: # LEFT
            bytes = b"\x1B[D"
        elif arg.keycode == 114: #RIGHT
            bytes = b"\x1B[C"
        else:
            bytes = None
        try:
            if bytes:
                self.serial.write(bytes)
            else:
                self.serial.write(arg.char.encode("utf-8"))
            #print(arg.char.encode("utf-8"), end="\r\n")
        except Exception as e:
            print("onTextKeyboard()",e.args)
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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        SerialFrame(port=sys.argv[1]).mainloop()
    else:
        SerialFrame().mainloop()

'''
notebook = ttk.Notebook(width=800, height=550)
notebook.pack(fill=tk.BOTH, expand=True)
frame1 = SerialFrame(master=notebook, port="/dev/ttyACM1")
frame2 = SerialFrame(master=notebook, port="/dev/ttyACM2")
notebook.add(frame1, text=frame1.fPort(none=False))
notebook.add(frame2, text=frame2.fPort(none=False))
notebook.mainloop()
'''
'''
app = tk.Tk()
frame = SerialFrame(master=app, port="/dev/ttyACM1")
app.mainloop()
'''
'''
SerialFrame(port="/dev/ttyACM1").mainloop()
'''
