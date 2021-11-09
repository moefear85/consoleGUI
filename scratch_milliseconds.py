from time import ctime,sleep,time

t=1636460718.999504
#print(t%1)
#print(round(t%1*1000)%1000)
#print(f"{round(t%1*1000)%1000:03d}")

while True:
    t=time()
    value=(f"{round(t%1*1000)%1000:03d}")
    print(value)
    if len(value)>3:
        print(value,t)
        sleep(1000)
