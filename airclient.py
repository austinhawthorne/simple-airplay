#!/usr/bin/env python3
import socket
import threading
import time
import random
import curses
from collections import deque
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange

SERVICE_TYPE = "_airplay._tcp.local."
services = {}

def on_service_state_change(zeroconf, service_type, name, state_change):
    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            services[name] = (ip, info.port)

def discover_service(timeout=2):
    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, SERVICE_TYPE, handlers=[on_service_state_change])
    time.sleep(timeout)
    zeroconf.close()
    return services

def send_packets(sock, data_queue, stop_event):
    while not stop_event.is_set():
        size = random.randint(100, 1000)
        data = bytes(random.getrandbits(8) for _ in range(size))
        try:
            sock.sendall(data)
            data_queue.append((time.time(), len(data)))
        except:
            stop_event.set()
            break
        time.sleep(0.1)

def draw_chart(stdscr, data_queue, stop_event):
    curses.curs_set(0)
    stdscr.nodelay(True)
    max_y, max_x = stdscr.getmaxyx()
    start_y = 1
    chart_height = max_y - start_y - 1
    data_history = deque(maxlen=max_x - 1)
    while not stop_event.is_set():
        stdscr.clear()
        now = time.time()
        # Header
        stdscr.addstr(0, 0, "Streaming random packets...")
        # Calculate bytes in last second
        bytes_last = sum(d for t, d in data_queue if now - t < 1)
        data_history.append(bytes_last)
        # Draw horizontal scrolling chart
        for x, val in enumerate(data_history):
            bar_height = min(int(val / 100), chart_height)
            for y in range(bar_height):
                stdscr.addch(max_y - 2 - y, x, '█')
        stdscr.refresh()
        time.sleep(1)

def main():
    found = discover_service()
    if not found:
        print("No AirPlay services found.")
        return
    print("Discovered services:")
    for idx, name in enumerate(found):
        ip, port = found[name]
        print(f"[{idx}] {name} -> {ip}:{port}")
    choice = int(input("Select service index: "))
    name = list(found)[choice]
    ip, port = found[name]
    print(f"Connecting to {ip}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    print("Connected! Streaming fake packets...")
    data_queue = deque()
    stop_event = threading.Event()
    send_thread = threading.Thread(target=send_packets, args=(sock, data_queue, stop_event))
    send_thread.daemon = True
    send_thread.start()
    curses.wrapper(lambda stdscr: draw_chart(stdscr, data_queue, stop_event))
    sock.close()

if __name__ == "__main__":
    main()

