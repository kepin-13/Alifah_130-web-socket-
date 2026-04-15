import socket
import threading
import requests
import html
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote_plus

HOST = 'localhost'
PORT = 8081

db_berita = [
    {"id": 1, "judul": "Project Web Server Socket Informatika", "link": "https://news.detik.com"},
]

def bersihkan_teks(teks):
    """Menghapus karakter aneh dan merapikan teks"""
    teks = html.unescape(teks)
    return teks.replace('"', '').replace("'", "").strip()

def ambil_data_detik():
    url = "https://news.detik.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        data = []
        for a in soup.find_all("a"):
            t, h = a.text.strip(), a.get("href")
            if t and h and "detik.com" in h and len(t) > 30:
                data.append({"judul": bersihkan_teks(t), "link": h})
        return data[:8] 
    except: return []

def handle_client(client_socket, addr):
    global db_berita
    try:
        data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        if not data: return
        
        first_line = data.split('\r\n')[0].split(' ')
        method, path_full = first_line[0], first_line[1]
        parsed = urlparse(path_full)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        body = ""
        if method == "POST":
            body_parts = data.split('\r\n\r\n')
            if len(body_parts) > 1: body = parse_qs(body_parts[1])

        # --- ROUTING ---

        # 1. READ (Halaman Utama)
        if path == '/':
            rows = ""
            for b in db_berita:
                rows += f"""<tr>
                    <td>{b['id']}</td>
                    <td>{b['judul']}</td>
                    <td><a href="{b['link']}" target="_blank" style="color:#007bff; text-decoration:none;">Lihat Berita</a></td>
                    <td>
                        <a href="/edit-page?id={b['id']}" class="btn-sm btn-edit">Edit</a>
                        <a href="/delete?id={b['id']}" class="btn-sm btn-del" onclick="return confirm('Yakin hapus berita ini?')">Hapus</a>
                    </td>
                </tr>"""
            
            content = f"""
            <html><head><title>Alifah_130</title>
            <style>
                body{{font-family:'Segoe UI', sans-serif; margin:40px; background:#f4f7f6; color:#333;}}
                .card{{background:white; padding:30px; border-radius:15px; box-shadow:0 10px 25px rgba(0,0,0,0.05);}}
                h1{{margin-bottom:5px; color:#2c3e50;}}
                .info{{margin-bottom:25px; font-size:14px; color:#666;}}
                table{{width:100%; border-collapse:collapse; background:white; margin-top:20px;}}
                th,td{{padding:15px; border-bottom:1px solid #eee; text-align:left;}}
                th{{background:#f8f9fa; color:#2c3e50; font-weight:600;}}
                .form-tambah{{background:#f9f9f9; padding:20px; border-radius:10px; margin-bottom:20px; border:1px solid #eee;}}
                .input-group{{margin-bottom:10px;}}
                input[type="text"]{{width:100%; padding:10px; border:1px solid #ddd; border-radius:5px;}}
                .btn{{padding:12px 24px; color:white; text-decoration:none; border-radius:8px; background:#27ae60; border:none; font-weight:bold; cursor:pointer;}}
                .btn-manual{{background:#3498db; margin-top:10px;}}
                .btn-sm{{padding:6px 12px; color:white; text-decoration:none; border-radius:5px; font-size:12px; font-weight:bold;}}
                .btn-edit{{background:#f39c12;}}
                .btn-del{{background:#e74c3c;}}
            </style></head>
            <body><div class="card">
                <h1>Socket Dan Scraping Berita</h1>
                <div class="info">
                    Nama: <b>Alifah Oktavina Putri Sahri</b><br>
                    NIM: <b>241080200130</b>
                </div>

                <div class="form-tambah">
                    <h3>Tambah Berita Terbaru</h3>
                    <form method="POST" action="/tambah-manual">
                        <div class="input-group">
                            <input type="text" name="judul" placeholder="masukan judul berita   " required>
                        </div>
                        <div class="input-group">
                            <input type="text" name="link" placeholder="Masukkan URL (Contoh: https://kompas.com)" required>
                        </div>
                        <button type="submit" class="btn btn-manual">Simpan Berita Terbaru</button>
                    </form>
                </div>

                <a href="/auto-scrape" class="btn"> AMBIL BERITA OTOMATIS </a>

                <table>
                    <tr><th>ID</th><th>Judul Berita</th><th>Link URL</th><th>Aksi</th></tr>
                    {rows if rows else "<tr><td colspan='4' align='center'>Data Kosong</td></tr>"}
                </table>
            </div></body></html>"""
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{content}"

        # 2. CREATE MANUAL
        elif path == '/tambah-manual' and method == 'POST':
            new_id = max([b['id'] for b in db_berita] + [0]) + 1
            judul_man = bersihkan_teks(unquote_plus(body.get('judul', [''])[0]))
            link_man = unquote_plus(body.get('link', [''])[0])
            if judul_man and link_man:
                db_berita.append({"id": new_id, "judul": judul_man, "link": link_man})
            response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"

        # 3. AUTO-SCRAPE
        elif path == '/auto-scrape':
            for h in ambil_data_detik():
                new_id = max([b['id'] for b in db_berita] + [0]) + 1
                db_berita.append({"id": new_id, "judul": h['judul'], "link": h['link']})
            response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"

        # 4. HALAMAN EDIT
        elif path == '/edit-page':
            idx = int(query.get('id', [0])[0])
            berita = next((b for b in db_berita if b['id'] == idx), None)
            content = f"""
            <html><body style="font-family:sans-serif; padding:40px; background:#f4f7f6;">
                <div style="max-width:500px; margin:auto; background:white; padding:25px; border-radius:12px; box-shadow:0 5px 15px rgba(0,0,0,0.1);">
                    <h3>Edit Data Berita</h3>
                    <form method="POST" action="/update?id={idx}">
                        <label>Judul:</label><br>
                        <textarea name="judul" rows="4" style="width:100%; margin-top:5px; border:1px solid #ddd; border-radius:5px; padding:10px;">{berita['judul']}</textarea><br><br>
                        <label>URL Link:</label><br>
                        <input type="text" name="link" value="{berita['link']}" style="width:100%; margin-top:5px; border:1px solid #ddd; border-radius:5px; padding:10px;"><br><br>
                        <button type="submit" style="background:#27ae60; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer;">Simpan Perubahan</button>
                        <a href="/" style="margin-left:10px; color:#666;">Batal</a>
                    </form>
                </div>
            </body></html>"""
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{content}"

        # 5. UPDATE
        elif path == '/update' and method == 'POST':
            idx = int(query.get('id', [0])[0])
            for b in db_berita:
                if b['id'] == idx:
                    b['judul'] = bersihkan_teks(unquote_plus(body.get('judul', [''])[0]))
                    b['link'] = unquote_plus(body.get('link', [''])[0])
            response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"

        # 6. DELETE
        elif path == '/delete':
            idx = int(query.get('id', [0])[0])
            db_berita = [b for b in db_berita if b['id'] != idx]
            response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"

        client_socket.sendall(response.encode('utf-8'))
    except Exception as e: print(f"Error: {e}")
    finally: client_socket.close()

def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Server Running: http://{HOST}:{PORT}")
    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c, a)).start()

if __name__ == "__main__":
    start()