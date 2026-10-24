from flask import Flask, request, send_file, render_template_string
from rembg import remove, new_session
from PIL import Image
import io

app = Flask(__name__)

# ছোট CPU মডেল — Free Render এ চলার সম্ভাবনা বেশি
session = new_session("u2net")

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Background Remover</title>
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
    body {
        background: linear-gradient(135deg, #667eea, #764ba2);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    .container {
        background: white;
        border-radius: 20px;
        padding: 32px 24px;
        max-width: 560px;
        width: 100%;
        box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        text-align: center;
    }
    h1 { color: #333; margin-bottom: 8px; font-size: 26px; }
    p.subtitle { color: #777; margin-bottom: 22px; }
    #dropZone {
        border: 3px dashed #764ba2;
        border-radius: 15px;
        padding: 36px 16px;
        cursor: pointer;
        background: #f9f9ff;
        min-height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }
    #dropZone:hover, #dropZone.dragover { background: #efeaff; }
    #dropZone p { color: #666; font-size: 15px; }
    #dropZone span { font-size: 36px; margin-bottom: 8px; }
    #preview-area { display: none; margin-top: 20px; }
    #imgPreview {
        max-width: 100%;
        max-height: 280px;
        border-radius: 10px;
        background: repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50% / 16px 16px;
    }
    .btn-group { margin-top: 18px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
    button, a.download-btn {
        padding: 12px 22px; border: none; border-radius: 8px; font-size: 15px;
        cursor: pointer; font-weight: 600; text-decoration: none;
        display: inline-flex; align-items: center; gap: 6px;
    }
    #removeBtn { background: #764ba2; color: white; }
    #removeBtn:disabled { background: #ccc; cursor: not-allowed; }
    .download-btn { background: #28a745; color: white; }
    #resetBtn { background: #eee; color: #333; }
    .loader { display: none; margin-top: 12px; color: #764ba2; font-weight: 600; }
    .spinner {
        border: 4px solid #eee; border-top: 4px solid #764ba2;
        border-radius: 50%; width: 28px; height: 28px;
        animation: spin 1s linear infinite; margin: 8px auto;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="container">
    <h1>🖼️ Background Remover</h1>
    <p class="subtitle">ছবি Paste (Ctrl+V) করুন বা Upload করুন</p>
    <div id="dropZone">
        <span>📋</span>
        <p><b>এখানে ছবি Paste করুন</b><br>অথবা Click / Drag & Drop</p>
        <input type="file" id="fileInput" accept="image/*" style="display:none;">
    </div>
    <div id="preview-area">
        <img id="imgPreview" src="">
        <div class="loader" id="loader">
            <div class="spinner"></div>
            Background Remove হচ্ছে... ৩০–৬০ সেকেন্ড লাগতে পারে
        </div>
        <div class="btn-group">
            <button id="removeBtn">✂️ Remove Background</button>
            <a id="downloadBtn" class="download-btn" style="display:none;" download="no-bg.png">⬇️ Download</a>
            <button id="resetBtn">🔄 নতুন ছবি</button>
        </div>
    </div>
</div>
<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const previewArea = document.getElementById('preview-area');
const imgPreview = document.getElementById('imgPreview');
const removeBtn = document.getElementById('removeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');
const loader = document.getElementById('loader');
let currentFile = null;

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => { if (e.target.files.length) handleFile(e.target.files[0]); });
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault(); dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
document.addEventListener('paste', e => {
    for (let item of e.clipboardData.items) {
        if (item.type.indexOf('image') !== -1) { handleFile(item.getAsFile()); break; }
    }
});
function handleFile(file) {
    currentFile = file;
    imgPreview.src = URL.createObjectURL(file);
    dropZone.style.display = 'none';
    previewArea.style.display = 'block';
    downloadBtn.style.display = 'none';
    removeBtn.style.display = 'inline-flex';
}
removeBtn.addEventListener('click', async () => {
    if (!currentFile) return;
    loader.style.display = 'block';
    removeBtn.disabled = true;
    const formData = new FormData();
    formData.append('image', currentFile);
    try {
        const response = await fetch('/remove-bg', { method: 'POST', body: formData });
        if (!response.ok) throw new Error('Server Error');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        imgPreview.src = url;
        downloadBtn.href = url;
        downloadBtn.style.display = 'inline-flex';
        removeBtn.style.display = 'none';
    } catch (err) {
        alert('❌ কিছু ভুল হয়েছে। ছোট ছবি দিয়ে আবার চেষ্টা করুন।');
    } finally {
        loader.style.display = 'none';
        removeBtn.disabled = false;
    }
});
resetBtn.addEventListener('click', () => {
    currentFile = null; fileInput.value = '';
    dropZone.style.display = 'flex'; previewArea.style.display = 'none';
});
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
    img = Image.open(file.stream).convert('RGBA')

    # RAM বাঁচাতে বড় ছবি ছোট করা
    max_size = 800
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    output = remove(img, session=session)

    buf = io.BytesIO()
    output.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
