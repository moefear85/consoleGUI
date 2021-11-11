from tkinter import Text,LEFT,RIGHT,TOP,BOTH,BOTTOM,END,INSERT,ALL
import random,string

chars = "eNrFWmtXG8kR/SssYLPrPE635t\nl2jCVWQgiMY++xl9hHxDvTM0O82SUBCxsn0X9P33poRgLJm0/5IJBmerqrq27devT8e29W3872Hm+Ve9NbY6e3NnzKLHzHx/x0PL31efgWTW8LN73N6erDcLF4Ef6kP4Q/cbiU\
hv/1dvjj5emYnp7eNtXbDHMUz8If8zzMH83CV\ndxuptfT29qEX71+OdwJC+S7LEPZm0xvq97wYLIdnjVJERbuhU8Ym+f98Cea7k0vsQLmuwkzJDQfjXLZPFwNC9RBZuvClybc8UH4ssmmeyTXf07CuCqML/nZpsmy\
NTd06QGrhnYaPlWV0U55Pgifis56C+WFT1CdCx8\nf4f/3c5ElP8Me+xB+1K5jwv/cDVgF9y/qns1laV6h35FBV2p/W/89DMCzh/XuTg2Lxdkw/C2DfVzE8waLBhs5f6Irw97hoSI87JvzzLI6bcR25uE2PwqLVOMw\
s/TbXPxF8Jy+fIieeIpaJkVXPJ006Iqnx4dw9\n/TkIQrq9Dluoy/eO687fXGiAbP3+y16ffL9x1lxjZcorcmy2No8NuFOfTm7/rK4GEW9PFysilmhb1sCVsGf9uRydxbTc4nL0vl/AZcQ2NA"

def func():
    global t
    lineCount = int(t.index("end").split(".")[0])
    print(lineCount)

t = Text()
t.insert(END,chars)
lineCharCount = t.index("end-1c")
lineCount=int(t.index("end-1c").split(".")[0])
lastLineCharCount=int(t.index("end-1c").split(".")[1])
lastLine=t.get(f'{t.index("end-1c").split(".")[0]}.0',END)
print(lastLine)
count=5
print(f"Deleting last {count} chars. Result:")
t.delete(f"end-{1+count}c","end")
lastLine=t.get(f'{t.index("end-1c").split(".")[0]}.0',END)
print(lastLine)
#t.insert(END,chars)
#t.after_idle(func)
#t.pack()
#t.mainloop()