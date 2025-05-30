#!/usr/bin/env python3
import socket
import threading
import time
from collections import deque
import curses
from zeroconf import ServiceInfo, Zeroconf

SERVICE_TYPE    = "_airplay._tcp.local."
SERVICE_NAME    = "Test AirPlay._airplay._tcp.local."
PORT            = 7000
ANN_INTERVAL    = 5  # seconds

def announcement_loop(zeroconf, info, announcements, stop_event):
    while not stop_event.is_set():
        time.sleep(ANN_INTERVAL)
        try:
            # Force an mDNS announcement on the network
            zeroconf.update_service(info)
            announcements.append(time.time())
        except Exception:
            pass

def tcp_server(data_queue, stop_event):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("", PORT))
    srv.listen(1)
    print(f"Listening on port {PORT}…")
    conn, addr = srv.accept()
    print("Client connected:", addr)
    while not stop_event.is_set():
        try:
            data = conn.recv(4096)
            if not data:
                break
            data_queue.append((time.time(), len(data)))
        except:
            break
    conn.close()
    stop_event.set()

def draw_chart(stdscr, data_queue, announcements, stop_event):
    curses.curs_set(0)
    stdscr.nodelay(True)
    max_y, max_x = stdscr.getmaxyx()
    start_y      = 3
    chart_height = max_y - start_y - 1
    data_history = deque(maxlen=max_x - 1)

    while not stop_event.is_set():
        stdscr.clear()
        now = time.time()

        # Header with service info
        stdscr.addstr(0, 0, f"Service: {SERVICE_NAME} on port {PORT}")
        # Last announcement timestamp
        if announcements:
            last = announcements[-1]
            ts   = time.strftime("%H:%M:%S", time.localtime(last))
            stdscr.addstr(1, 0, f"Last announcement: {ts}")

        # Compute bytes in the last second
        bytes_last = sum(d for t, d in data_queue if now - t < 1)
        data_history.append(bytes_last)

        # Draw horizontal, scrolling bar chart
        for x, val in enumerate(data_history):
            bar_height = min(int(val / 256), chart_height)
            for y in range(bar_height):
                stdscr.addch(max_y - 2 - y, x, '█')

        stdscr.refresh()
        time.sleep(1)

def main():
    zeroconf = Zeroconf()
    desc = {'txtvers': '1', 'device': 'Test AirPlay'}
    info = ServiceInfo(
        SERVICE_TYPE,
        SERVICE_NAME,
        addresses=[socket.inet_aton("127.0.0.1")],
        port=PORT,
        properties=desc
    )

    # Initial registration
    zeroconf.register_service(info)

    data_queue    = deque()
    announcements = deque(maxlen=5)
    announcements.append(time.time())
    stop_event    = threading.Event()

    # Start announcement thread
    ann_thread = threading.Thread(
        target=announcement_loop,
        args=(zeroconf, info, announcements, stop_event),
    )
    ann_thread.daemon = True
    ann_thread.start()

    # Start TCP server thread
    srv_thread = threading.Thread(
        target=tcp_server,
        args=(data_queue, stop_event),
    )
    srv_thread.start()

    # Launch the curses-based UI
    curses.wrapper(lambda stdscr: draw_chart(stdscr, data_queue, announcements, stop_event))

    # Clean up
    zeroconf.unregister_service(info)
    zeroconf.close()

if __name__ == "__main__":
    main()
