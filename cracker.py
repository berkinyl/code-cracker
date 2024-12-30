import hashlib
import asyncio
import aiohttp
from multiprocessing import Process, Value, Lock
import socket
import sys

LOG_SERVER = ("127.0.0.1", 9999)

url_get = "http://127.0.0.1:5000/get_password"
url_post = "http://127.0.0.1:5000/check_password"


# Log mesajlarını socket ile UDP üzerinden asenkron olarak gönderme
# (I/O bir işlemdir, bu yüzden CPU idleye düşmemesi için asenkron gerçekleşir.)
async def log_message_socket(message):
    loop = asyncio.get_event_loop()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        await loop.run_in_executor(None, sock.sendto, message.encode(), LOG_SERVER)


# API'den get isteği ile hedef şifrenin hashini alma
# (I/O bir işlemdir, bu yüzden CPU idleye düşmemesi için asenkron gerçekleşir.)
async def fetch_password():
    async with aiohttp.ClientSession() as session:
        async with session.get(url_get) as response:
            if response.status == 200:
                json_data = await response.json()
                print(f"Alınan hash: {json_data['password']}")  # Hash'i terminale yazdır
                return json_data["password"]
            else:
                raise Exception(f"API'den şifre hash'i alınamadı: {response.status} - {await response.text()}")


# Şifreyi post isteği göndererek doğrulamak için API'ye gönderme
# (I/O bir işlemdir, bu yüzden CPU idleye düşmemesi için asenkron gerçekleşir.)
async def validate_password(password):
    async with aiohttp.ClientSession() as session:
        async with session.post(url_post, json={"password": password}) as response:
            json_data = await response.json()
            return json_data.get("message") == "Success"


# MD5 hash oluşturma fonksiyonu
def text_to_md5(text):
    return hashlib.md5(text.encode()).hexdigest()


# 6 haneli rakamlardan oluşan şifre adaylarını oluşturma fonksiyonu
def generate_text(start, end):
    for number in range(start, end):
        yield f"{number:06d}"  # 6 haneli sıfır doldurulmuş sayı


# Deneme sayısını izlemek için bir Value değişkeni olarak tanımlama
global_counter = Value('i', 1)
lock = Lock()


# Tek süreçte şifre kırma
def single_process(start, end, pwd, flag):
    global global_counter, lock

    async def process_range():
        for text in generate_text(start, end):
            if flag.value == 1:
                return

            # Küresel sayaç için kilit kullanarak numara al
            with lock:
                count = global_counter.value
                global_counter.value += 1

            # Küresel sayaç değerini tek bir satırda yazdır
            sys.stdout.write(f"\r[GLOBAL_COUNTER]: {global_counter.value}")
            sys.stdout.flush()

            # Hash oluştur ve logla
            hashed = text_to_md5(text)
            await log_message_socket(f"Deneme #{count}: {text} (hash: {hashed})")

            # Şifre doğrulama
            if hashed == pwd:
                is_valid = await validate_password(text)  # POST isteği burada çağrılıyor
                if is_valid:
                    flag.value = 1
                    print(f"\nKırılan şifre: {text} Deneme: #{count}")
                    await log_message_socket(f"Kırılan şifre: {text}")
                    return

    asyncio.run(process_range())


# Ana fonksiyon
async def main():
    processes = []
    flag = Value('i', 0)

    # API'den hash alma
    try:
        pwd = await fetch_password()
    except Exception as e:
        print(f"Hash alma hatası: {e}")
        return

    # 6 haneli şifreler için başlangıç ve bitiş aralığı
    num_threads = 12
    min_number = 1
    max_number = 10**6
    range_size = (max_number - min_number) // num_threads

    for i in range(num_threads):
        start = min_number + i * range_size
        end = min_number + (i + 1) * range_size if i < num_threads - 1 else max_number
        process = Process(
            target=single_process,
            args=(start, end, pwd, flag),
        )
        processes.append(process)
        processes[-1].start()

    for process in processes:
        process.join()

if __name__ == "__main__":
    asyncio.run(main())