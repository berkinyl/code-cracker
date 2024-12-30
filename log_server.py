import socket

# Log sunucusu
def log_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(("127.0.0.1", 9999))  # Sunucuyu başlat
        print("Log sunucusu çalışıyor ve log mesajlarını alıyor...")

        while True:
            message, _ = server_socket.recvfrom(1024)  # Mesaj al
            print(message.decode("utf-8"))  # Gelen log mesajını terminale yazdır

if __name__ == "__main__":
    log_server()

