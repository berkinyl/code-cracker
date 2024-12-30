from flask import Flask, request, jsonify
import hashlib
import random
import json

app = Flask(__name__)

# Şifre üretme fonksiyonu
def generate_password():
    # 6 haneli sadece rakamlardan oluşan bir şifre üret
    password = "".join(random.choices("0123456789", k=6))  # 6 haneye güncellendi
    print(f"Oluşturulan şifre (hashlenmeden önce): {password}")  # Konsola yazdır
    return password


@app.route("/get_password", methods=["GET"])
def get_password():
    # Şifre oluştur ve hashle
    password = generate_password()
    password_hash = hashlib.md5(password.encode()).hexdigest()

    # Hashlenmiş şifreyi döndür ve hem hash'i hem de açık şifreyi dosyaya yaz
    with open("password.json", "w") as f:
        json.dump({"password": password, "hash": password_hash}, f, indent=4)  # Şifre ve hash yazılıyor

    # JSON yanıt olarak sadece hash döndürülüyor
    return jsonify({"password": password_hash})


@app.route("/check_password", methods=["POST"])
def check_password():
    # Gelen veriden şifreyi al
    data = request.get_json()
    password = data.get("password")
    password_hash = hashlib.md5(password.encode()).hexdigest()

    # Kaydedilen hash'i dosyadan oku
    try:
        with open("password.json", "r") as f:
            stored_data = json.load(f)
            stored_hash = stored_data.get("hash")
    except FileNotFoundError:
        return jsonify({"message": "Error", "detail": "Password file not found"}), 500

    # Hash doğrulaması yap
    if password_hash == stored_hash:
        return jsonify({"message": "Success"})
    else:
        return jsonify({"message": "Failed"})


if __name__ == "__main__":
    app.run()
