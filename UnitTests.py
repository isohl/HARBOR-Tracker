from harbor import *


def RandomWalk():
    dontDie = True
    mainlock = Lock()
    h = Harbor(mainlock,state=True)    
    def src():
        while dontDie:
            with mainLock:
                if len(h.paths['Car 1']) > 0:
                    last_point = h.paths['Balloon'][-1]
                    last_d710_point = h.paths['Car 1'][-1]
                else:
                    h.addCallsign("WB1SAR-11", "Balloon")
                    h.addCallsign("KF7WII-11", "Balloon")
                    h.addCallsign("KE7ROS-11", "Balloon")
                    h.addCallsign("D710", "Car 1")
                    last_d710_point = Point(time.time(),40.191484, -110.385534,1000)
                    h.newPoint("D710", last_d710_point)
                    last_point = Point(time.time(),40.191584, -110.385634, 1000)
                    h.newPoint("WB1SAR-11", last_point)
    
                h.readouts['ascent'] += randint(-10, 10)
                last_point = Point(time.time(), last_point.latitude + float(randint(-2, 4))/1000, last_point.longitude + float(randint(-2, 6))/1000,1000)
                h.newPoint("WB1SAR-11", last_point)
                last_d710_point = Point(time.time(), last_d710_point.latitude + float(randint(-2, 4))/1000, last_d710_point.longitude + float(randint(-2, 6))/1000,1000)
                h.newPoint("D710", last_d710_point)
            time.sleep(3)
    t = Thread(target=src)
    t.daemon = True
    t.start()    
    
    httpd = HTTPServer(('', 8001), handler(h))
    httpd.serve_forever()

    dontDie = False    
