import os
import tempfile
from flask import Flask, render_template_string, request, send_file, flash
from git import Repo
import shutil
import zipfile
import re

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>GitHub 文件下载器</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background-color: #f4f4f4;
            color: #333;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }

        .container {
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            width: 80%;
            max-width: 600px;
            text-align: center;
        }

        h1 {
            color: #333;
            margin-bottom: 20px;
        }

        .description {
            color: #777;
            margin-bottom: 30px;
            text-align: left;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            margin-bottom: 20px;
            text-align: left;
        }
        .form-group label {
            text-align: left;
        }

        input[type="text"] {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 10px;
            box-sizing: border-box;
            width: 100%;
        }

        .button {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .button:hover {
            background-color: #0056b3;
        }
         .flashes {
            list-style: none;
            padding: 0;
            margin-top: 20px;
            text-align: center;
        }

        .flashes li {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            display: inline-block;
        }

        .flashes li.success {
            background: #d4edda;
            color: #155724;
        }
        footer {
            margin-top: 40px;
            text-align: center;
            color: #777;
            padding: 10px;
        }
        footer a {
            color: #007bff;
            text-decoration: none;
        }
        footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>GitHub 文件下载器</h1>
        <form method="post">
            <div class="form-group">
                <label for="repo_path">GitHub 链接:</label>
                <input type="text" id="repo_path" name="repo_path" required>
            </div>
            <div class="form-group">
                <label for="github_token">GitHub Personal Access Token (可选):</label>
                <input type="text" id="github_token" name="github_token">
            </div>
            <button type="submit" class="button">下载</button>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                  <ul class=flashes>
                  {% for category, message in messages %}
                    <li class="{{ category }}">{{ message }}</li>
                  {% endfor %}
                  </ul>
                {% endif %}
            {% endwith %}
        </form>
          <p class="description">
            <br>
            <strong>使用说明：</strong>
            <br>
            <small>输入 GitHub 仓库链接和文件路径即可打包下载。</small>
            <br>
            <small>例如：https://github.com/ssfun/download-github-files/tree/main/templates</small>
            <br>
            <small>对于私有仓库，请提供 GitHub Personal Access Token.</small>
            <br>
            <strong>隐私声明：</strong> 
            <br>
            <small>本项目不会记录用户的任何信息，包括 GitHub 链接、Personal Access Token 以及下载的文件内容。所有操作均在本地完成，不存储任何数据。</small>
        </p>
    </div>
    <footer>
        <a href="https://github.com/ssfun/download-github-files">GitHub 文件下载器</a> 由 <a href="https://github.com/ssfun">ssfun</a> 构建，源代码遵循 <a href="https://opensource.org/license/mit">MIT 协议</a>
    </footer>
</body>
</html>
"""


def download_github_files(repo_url, file_paths, github_token=None):
    """从GitHub仓库下载指定路径的文件，并打包成zip。"""
    try:
        temp_dir = tempfile.mkdtemp()
        repo_name = repo_url.split('/')[-1].replace(".git", "")
        local_repo_path = os.path.join(temp_dir, repo_name)
        
        # 克隆仓库
        if github_token:
            repo_url_with_token = repo_url.replace("https://", f"https://{github_token}@")
            Repo.clone_from(repo_url_with_token, local_repo_path)
        else:
            Repo.clone_from(repo_url, local_repo_path)

        zip_file_path = os.path.join(temp_dir, f"{repo_name}_files.zip")
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in file_paths:
                abs_file_path = os.path.join(local_repo_path, file_path)
                if os.path.exists(abs_file_path) and os.path.isfile(abs_file_path):
                    zf.write(abs_file_path, os.path.basename(abs_file_path))
                elif os.path.exists(abs_file_path) and os.path.isdir(abs_file_path):
                    for root, dirs, files in os.walk(abs_file_path):
                        for file in files:
                            file_abs_path = os.path.join(root, file)
                            zf.write(file_abs_path, os.path.relpath(file_abs_path, local_repo_path))

        shutil.rmtree(local_repo_path)
        if os.path.exists(zip_file_path) and os.path.getsize(zip_file_path) > 0:
            return zip_file_path, f"{repo_name}_files.zip"
        else:
            return None, None
    except Exception:
        return None, None

def parse_github_url(url):
    """解析 GitHub URL，提取仓库 URL 和文件路径。"""
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)(.*)', url)
    if match:
        owner, repo, branch, path = match.groups()
        repo_url = f'https://github.com/{owner}/{repo}.git'
        file_paths = [path.lstrip('/')] if path else []
        return repo_url, file_paths
    else:
        return None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        repo_path = request.form.get('repo_path')
        github_token = request.form.get('github_token')
        if not repo_path:
            flash('请提供 GitHub 链接', 'error')
            return render_template_string(HTML_TEMPLATE)

        repo_url, file_paths = parse_github_url(repo_path)
        if not repo_url:
             flash('无效的 GitHub 链接', 'error')
             return render_template_string(HTML_TEMPLATE)

        zip_path, zip_filename = download_github_files(repo_url, file_paths, github_token)
        if zip_path:
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        else:
            flash('下载失败，请检查链接和文件路径。', 'error')
            return render_template_string(HTML_TEMPLATE)

    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 3000))
    app.run(debug=True, host="0.0.0.0", port=port)
