from tkinter import Text,LEFT,RIGHT,TOP,BOTH,BOTTOM,END,INSERT,ALL
import random,string

chars = "eNrFWmtXG8kR/SssYLPrPE635tl2jCVWQgiMY++xl9hHxDvTM0O82SUBCxsn0X9P33poRgLJm0/5IJBmerqrq27devT8e29W3872Hm+Ve9NbY6e3NnzKLHzHx/x0PL31efgWTW8LN73N6erDcLF4Ef6kP4Q/cbiU\
hv/1dvjj5emYnp7eNtXbDHMUz8If8zzMH83CVdxuptfT29qEX71+OdwJC+S7LEPZm0xvq97wYLIdnjVJERbuhU8Ym+f98Cea7k0vsQLmuwkzJDQfjXLZPFwNC9RBZuvClybc8UH4ssmmeyTXf07CuCqML/nZpsmy\
NTd06QGrhnYaPlWV0U55Pgifis56C+WFT1CdCx8f4f/3c5ElP8Me+xB+1K5jwv/cDVgF9y/qns1laV6h35FBV2p/W/89DMCzh/XuTg2Lxdkw/C2DfVzE8waLBhs5f6Irw97hoSI87JvzzLI6bcR25uE2PwqLVOMw\
s/TbXPxF8Jy+fIieeIpaJkVXPJ006Iqnx4dw9/TkIQrq9Dluoy/eO687fXGiAbP3+y16ffL9x1lxjZcorcmy2No8NuFOfTm7/rK4GEW9PFysilmhb1sCVsGf9uRydxbTc4nL0vl/AZcQ2NA"

chars=""
for x in range(500):
    chars+=random.choice(string.ascii_uppercase + string.digits)
i=0
def func():
    global t,i
    text=t.get("0.0",END)
    length=len(text)
    if length<100000:
        t.after(30,func)
    if i<20000:
        t.insert(END,chars)
    else:
        #t.insert(END,"\n")
        i=0
    t.see(END)
    print(length,i)
    i+=len(chars)

t = Text()
t.after_idle(func)
t.pack()
t.mainloop()