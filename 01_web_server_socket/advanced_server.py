import socket
import threading
import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# Konfigurasi
HOST = 'localhost'
PORT = 8081
STATIC_DIR = 'www'

os.makedirs(STATIC_DIR, exist_ok=True)

# --- FUNGSI SCRAPING (DIAMBIL DARI Alifah_130.py) ---
def jalankan_scraping():
    url = "https://news.detik.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("a")
            
            data_berita = []
            seen_titles = set()

            for article in articles:
                judul = article.text.strip()
                link = article.get("href")
                if judul and link and "detik.com" in link and len(judul) > 20:
                    if judul not in seen_titles:
                        data_berita.append({"judul": judul, "link": link})
                        seen_titles.add(judul)
            return data_berita[:10] # Ambil 10 berita teratas untuk display
        return []
    except Exception as e:
        print(f"Scraping Error: {e}")
        return []

# --- CORE SERVER LOGIC ---
def parse_request(request_data):
    try:
        lines = request_data.split('\r\n')
        if not lines or not lines[0]: return None
        
        request_line = lines[0].split(' ')
        method, path = request_line[0], request_line[1]
        
        parsed_url = urlparse(path)
        return {
            'method': method,
            'path': parsed_url.path,
            'query_params': parse_qs(parsed_url.query)
        }
    except:
        return None

def send_response(client_socket, status_code, content_type, content):
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    header = f"HTTP/1.1 {status_code}\r\n"
    header += f"Content-Type: {content_type}\r\n"
    header += f"Content-Length: {len(content)}\r\n"
    header += "Connection: close\r\n\r\n"
    
    client_socket.sendall(header.encode('utf-8') + content)

def handle_client(client_socket, client_address):
    try:
        client_socket.settimeout(5)
        request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        parsed = parse_request(request_data)
        
        if not parsed:
            client_socket.close()
            return

        # ROUTING BARU: Scraping
        if parsed['path'] == '/scraping':
            berita_list = jalankan_scraping()
            
            # Membuat baris tabel dari data scraping
            rows = ""
            for idx, b in enumerate(berita_list, 1):
                rows += f"<tr><td>{idx}</td><td>{b['judul']}</td><td><a href='{b['link']}' target='_blank'>Buka Link</a></td></tr>"

            html = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Hasil Scraping Detik</title>
                <style>
                    body {{ font-family: sans-serif; margin: 40px; line-height: 1.6; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #27ae60; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>Hasil Scraping Berita Detik</h1>
                <div class="info">
                    <p><strong>Nama:</strong> Alifah Oktavina Putri Sahri</p>
                    <p><strong>NIM:</strong> 241080200130</p>
                </div>
                <table>
                    <tr><th>No</th><th>Judul Berita</th><th>Aksi</th></tr>
                    {rows if rows else "<tr><td colspan='3'>Gagal mengambil data atau data kosong.</td></tr>"}
                </table>
                <p><a href="/">Kembali ke Home</a></p>
            </body>
            </html>"""
            send_response(client_socket, "200 OK", "text/html", html)

        # Route Home
        elif parsed['path'] == '/' or parsed['path'] == '/index.html':
            html = """<!DOCTYPE html>
            <html>
            <head><title>Home Server</title></head>
            <body style="font-family: Arial; text-align: center; margin-top: 50px;">
                <h1>Selamat Datang di Web Server Socket</h1>
                <p>Silakan klik tombol di bawah untuk melakukan scraping berita:</p>
                <a href="/scraping" style="padding: 10px 20px; background: #27ae60; color: white; text-decoration: none; border-radius: 5px;">Mulai Scraping Berita</a>
            </body>
            </html>"""
            send_response(client_socket, "200 OK", "text/html", html)
            
        else:
            send_response(client_socket, "404 Not Found", "text/html", "<h1>404 Not Found</h1>")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    
    print(f"Server berjalan di http://{HOST}:{PORT}")
    
    try:
        while True:
            client_sock, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nServer Berhenti.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    run_server()