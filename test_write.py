import time

pointer1 = 0
pointer2 = 0

while True:
    f_w = open("JJI20200226.txt", "a")
    f_r = open("JJI20200224(copy).txt", "r")
    f_r.seek(pointer2)
    f_w.write(f_r.readline())
    pointer1 = f_w.tell()
    pointer2 = f_r.tell()
    f_w.close()
    f_r.close()
    time.sleep(0.5)
