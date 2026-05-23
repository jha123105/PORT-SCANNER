import socket
import threading
import time
from core.service_detection import get_service

class PortScanner:
    def __init__(self, target, port_start, port_end, syn=False, callback=None, log_callback=None):
        self.target = target
        self.start = port_start
        self.end = port_end
        self.syn = syn  # SYN scan not fully implemented; we'll use TCP connect for now
        self.callback = callback
        self.log = log_callback
        self.open_ports = []
        self.lock = threading.Lock()
    
    def scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((self.target, port))
            if result == 0:
                banner = self.get_banner(port)
                with self.lock:
                    self.open_ports.append((port, banner))
            sock.close()
        except:
            pass
    
    def get_banner(self, port):
        # Try to grab service banner
        service = get_service(port)
        if port in [21, 22, 23, 25, 80, 443, 3306, 5432]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.target, port))
                sock.send(b"\n")
                banner = sock.recv(256).decode('utf-8', errors='ignore').strip()
                sock.close()
                return f"{service} - {banner[:50]}"
            except:
                return service
        return service
    
    def scan(self):
        total = self.end - self.start + 1
        scanned = 0
        for port in range(self.start, self.end + 1):
            self.scan_port(port)
            scanned += 1
            if self.callback:
                self.callback(scanned, total, self.open_ports)
        if self.log:
            self.log(f"Scan complete. Open ports: {len(self.open_ports)}")