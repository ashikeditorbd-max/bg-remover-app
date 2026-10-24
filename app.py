from flask import Flask, request, send_file, render_template_string
from rembg import remove, new_session
from PIL import Image
import io

app = Flask(__name__)

# হালকা মডেল (u2netp) ব্যবহার করার জন্য সেশন তৈরি
session = new_session("u2netp")

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<title>Lite BG Remover</title>
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
    body { background: #f0f2f5; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
    .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; width: 100%; max-width: 400px; }
    h2 { margin-bottom: 20px; color: #333; }
    #preview { max-width: 100%; border-radius: 10px; margin: 20px 0; display: none; }
    .btn { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold; }
    .btn:disabled { background: #ccc; }
    input[type="file"] { margin-bottom: 15px; }
</style>
</head>
<body>
<div class="card">
    <h2>🖼️ Lite BG Remover</h2>
    <input type="file" id="fileInput" accept="image/*">
    <img id="preview" src="">
    <button id="runBtn" class="btn">Remove Background</button>
    <p id="status" style="margin-top:10px; color: #666;"></p>
    <a id="dl" style="display:none; color: green; font-weight: bold; text-decoration: none; display: block; margin-top: 15px;" download="no-bg.png">⬇️ Download Image</a>
</div>

<script>
    const fileInput = document.getElementById('fileInput');
    const preview = document.getElementById('preview');
    const runBtn = document.getElementById('runBtn');
    const status = document.getElementById('status');
    const dl = document.getElementById('dl');

    fileInput.onchange = e => {
        const file = e.target.files[0];
        if (file) {
            preview.src = URL.createObjectURL(file);
            preview.style.display = 'block';
            dl.style.display = 'none';
        }
    };

    runBtn.onclick = async () => {
        const file = fileInput.files[0];
        if (!file) return alert("ছবি সিলেক্ট করুন");

        runBtn.disabled = true;
        status.innerText = "প্রসেস হচ্ছে... (৩০-৬০ সেকেন্ড লাগতে পারে)";

        const fd = new FormData();
        fd.append('image', file);

        try {
            const res = await fetch('/remove-bg', { method: 'POST', body: fd });
            if (!res.ok) throw new Error();
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            preview.src = url;
            dl.href = url;
            dl.style.display = 'block';
            status.innerText = "সফল হয়েছে! ✅";
        } catch (e) {
            status.innerText = "সার্ভার লোড নিতে পারছে না। ছোট ছবি দিয়ে চেষ্টা করুন।";
        } finally {
            runBtn.disabled = false;
        }
    };
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/remove-bg', methods=['POST'])
def remove_bg():
    file = request.files['image']
    img = Image.open(file.stream).convert("RGBA")
    
    # মেমরি বাঁচাতে ছবি বড় হলে ছোট করে নেওয়া (Resize)
    img.thumbnail((800, 800)) 
    
    # u2netp মডেল ব্যবহার করে ব্যাকগ্রাউন্ড রিমুভ
    output = remove(img, session=session)

    io_buf = io.BytesIO()
    output.save(io_buf, 'PNG')
    io_buf.seek(0)
    return send_file(io_buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
