from flask import Flask, request, send_file, render_template_string
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
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
        padding: 40px;
        max-width: 600px;
        width: 100%;
        box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        text-align: center;
    }
    h1 {
        color: #333;
        margin-bottom: 10px;
        font-size: 28px;
    }
    p.subtitle {
        color: #777;
        margin-bottom: 25px;
    }
    #dropZone {
        border: 3px dashed #764ba2;
        border-radius: 15px;
        padding: 40px 20px;
        cursor: pointer;
        transition: 0.3s;
        background: #f9f9ff;
        min-height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }
    #dropZone:hover, #dropZone.dragover {
        background: #efeaff;
        border-color: #667eea;
    }
    #dropZone p { color: #666; font-size: 16px; }
    #dropZone span { font-size: 40px; display: block; margin-bottom: 10px; }
    #preview-area {
        display: none;
        margin-top: 25px;
    }
    #imgPreview {
        max-width: 100%;
        max-height: 300px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.15);
        background: repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50% / 20px 20px;
    }
    .btn-group {
        margin-top: 20px;
        display: flex;
        gap: 10px;
        justify-content: center;
        flex-wrap: wrap;
    }
    button, a.download-btn {
        padding: 12px 25px;
        border: none;
        border-radius: 8px;
        font-size: 15px;
        cursor: pointer;
        font-weight: 600;
        text-decoration: none;
        transition: 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    #removeBtn {
        background: #764ba2;
        color: white;
    }
    #removeBtn:hover { background: #5e3a85; }
    #removeBtn:disabled { background: #ccc; cursor: not-allowed; }
    .download-btn {
        background: #28a745;
        color: white;
    }
    .download-btn:hover { background: #1e7e34; }
    #resetBtn {
        background: #eee;
        color: #333;
    }
    #resetBtn:hover { background: #ddd; }
    .loader {
        display: none;
        margin-top: 15px;
        color: #764ba2;
        font-weight: 600;
    }
    .spinner {
        border: 4px solid #eee;
        border-top: 4px solid #764ba2;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin: 10px auto;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
</style>
</head>
<body>

<div class="container">
    <h1>🖼️ Background Remover</h1>
    <p class="subtitle">ছবি Paste (Ctrl+V) করুন বা Drag & Drop করুন</p>

    <div id="dropZone">
        <span>📋</span>
        <p><b>এখানে ছবি Paste করুন (Ctrl+V)</b><br>অথবা Click করে ছবি বেছে নিন<br>অথবা Drag & Drop করুন</p>
        <input type="file" id="fileInput" accept="image/*" style="display:none;">
    </div>

    <div id="preview-area">
        <img id="imgPreview" src="">
        <div class="loader" id="loader">
            <div class="spinner"></div>
            Background Remove হচ্ছে... ⏳
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
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

document.addEventListener('paste', (e) => {
    const items = e.clipboardData.items;
    for (let item of items) {
        if (item.type.indexOf('image') !== -1) {
            const file = item.getAsFile();
            handleFile(file);
            break;
        }
    }
});

function handleFile(file) {
    currentFile = file;
    const url = URL.createObjectURL(file);
    imgPreview.src = url;
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
        const response = await fetch('/remove-bg', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Server Error');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        imgPreview.src = url;

        downloadBtn.href = url;
        downloadBtn.style.display = 'inline-flex';
        removeBtn.style.display = 'none';

    } catch (err) {
        alert('❌ কিছু ভুল হয়েছে, আবার চেষ্টা করুন।');
        console.error(err);
    } finally {
        loader.style.display = 'none';
        removeBtn.disabled = false;
    }
});

resetBtn.addEventListener('click', () => {
    currentFile = null;
    fileInput.value = '';
    dropZone.style.display = 'flex';
    previewArea.style.display = 'none';
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
    input_image = Image.open(file.stream).convert("RGBA")
    output_image = remove(input_image)

    img_io = io.BytesIO()
    output_image.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
