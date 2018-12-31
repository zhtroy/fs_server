import socket
from multiprocessing import Process ,Pipe, Queue
from threading import Thread
import threading
from contextlib import closing
import socketserver
from datetime import datetime
import queue


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

def phoneThread(s,q):
    try:
        while True:
            data = s.recv(1024)
            print('recv: {}  at:{}'.format(data,datetime.now().time()))
            if not data:    #socket关闭后退出线程
                print('phone socket closed, quit thread')
                break   
            q.put(data)
    except:
        raise
    finally:
        s.close()
   

def phoneServer(port,q):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #with closing( socket.socket(socket.AF_INET, socket.SOCK_STREAM) ) as s:
        s.bind(('', port))
        s.listen()
        print('listening on: ', port)
        while True:
            conn, addr = s.accept()
            print('port: ' ,port,'Connected by', addr)
            t = Thread(target= phoneThread, args=(conn,q))
            t.start()
    except KeyboardInterrupt:
        return
    finally:
        s.close()
           

def boardThread(s,q):
    try:
        while True:
        
            data = q.get()
            s.send(data)
            print('send: ', data)
            
    except ConnectionAbortedError:
        print('board socket closed, quit thread')
    finally:
        s.close()

class BoardThread(StoppableThread):
    def __init__(self,socket, q):
        super().__init__()
        self._s = socket
        self._q = q
    
    def run(self):
        
        while True:
            if self.stopped():
                break
            try:
                data = self._q.get(timeout = 0.1)
            except queue.Empty:
                continue
           
            try:
                self._s.send(data)
            except ConnectionAbortedError:
                print('board socket closed')
                break

            print('send: ', data)

        print('close socket and quit thread')
        self._s.close()
                
        
        


def boardServer(port,q):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

   # with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM) ) as s:
        s.bind(('', port))
        s.listen(1)
        print('listening on: ', port)
        t = None
        while True:
            conn, addr = s.accept()
            print('port: ', port,'Connected by', addr)
            # 只允许一个板卡连接
            if t:
                print('close old connection: ')
                t.stop()
            
            t = BoardThread(conn,q)
            t.start()        
                    
    except KeyboardInterrupt:
        return
    finally:
        s.close()





if __name__ == '__main__':
    q = Queue()
    p1 = Thread(target=boardServer , args = (3000,q))
    p2 = Thread(target=phoneServer , args = (5000,q))

    p1.start()
    
    p2.start()


    p1.join()
    p2.join()



    



   




   