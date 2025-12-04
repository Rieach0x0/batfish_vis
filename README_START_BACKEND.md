# バックエンド起動方法 - 決定版

## 🚀 最も簡単な起動方法

### 方法1: PowerShellスクリプトを使用（Windows側から）

Windowsで PowerShellを開き：

```powershell
cd D:\batfish_vis
.\start_backend_wsl.ps1
```

このスクリプトが自動的に：
- 既存のuvicornプロセスを停止
- Pythonキャッシュをクリア
- PYTHONPATHを設定してバックエンドを起動（リロード有効）

### 方法2: WSLターミナルで直接起動

WSL Ubuntuターミナルで以下をコピー＆ペースト：

```bash
cd ~/batfish_vis/backend && source .venv/bin/activate && pkill -9 -f uvicorn 2>/dev/null; find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null && PYTHONPATH=$PWD uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 方法3: スタートアップスクリプトを使用

WSL Ubuntuターミナルで：

```bash
cd ~/batfish_vis/backend
./start_backend.sh
```

## ✅ 起動成功の確認

以下のメッセージが表示されれば成功：

```
INFO:     Will watch for changes in these directories: ['/home/k-kawabe/batfish_vis/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
{"asctime": "...", "levelname": "INFO", "name": "root", "message": "Structured logging initialized", "log_level": "DEBUG"}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "CORS middleware configured", ...}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "Exception handlers registered"}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "FastAPI application initialized", ...}
INFO:     Application startup complete.
```

**重要**: 最後の行 `Application startup complete.` が表示されること！

## ❌ エラーが出る場合

### ModuleNotFoundError: No module named 'src.exceptions'

**原因**: `PYTHONPATH`が設定されていません。

**解決策**: 上記の**方法1、2、または3**を使用してください。単に`uv run uvicorn src.main:app --reload`だけでは起動しません。

### Port 8000 already in use

**解決策**:
```bash
pkill -9 -f uvicorn
```

### Cannot connect to Batfish

**解決策**:
```bash
cd ~/batfish_vis
docker compose up -d
docker ps | grep batfish
```

## 🎯 スナップショット作成テスト

バックエンドが起動したら：

### 1. ブラウザでフロントエンドを開く

```
http://localhost:5173
```

### 2. ヘルスチェック

画面上部に緑の「Connected to Batfish」が表示されることを確認

### 3. スナップショット作成

1. **Select Files** または **Select Folder** を選択
2. `.cfg` ファイルを選択（または `D:\networks\example` フォルダ）
3. Snapshot Name: `test-success`
4. Network Name: `default`
5. **Create Snapshot** をクリック

### 4. 期待される結果

✅ **成功メッセージ**:
```
Snapshot "test-success" created successfully! Detected 13 devices.
```

✅ **バックエンドログ**（WSLターミナル）:
```json
{"levelname": "INFO", "message": "Snapshot creation request received", "snapshot": "test-success", "file_count": 13}
{"levelname": "INFO", "message": "All files saved successfully", "files_saved": 13}
{"levelname": "INFO", "message": "Creating Batfish snapshot", "snapshot": "test-success"}
{"levelname": "INFO", "message": "Batfish snapshot initialized", "snapshot": "test-success"}
{"levelname": "INFO", "message": "Snapshot created successfully", "device_count": 13, "parse_error_count": 0}
```

## 📝 重要なポイント

### なぜPYTHONPATHが必要か？

uvicornの`--reload`オプションは、ファイル変更を検知してサブプロセスを起動します。このサブプロセスがPythonモジュールを正しくインポートするために、`PYTHONPATH`を明示的に設定する必要があります。

### リロード機能について

`--reload`オプションを使うと：
- ✅ ファイルを保存すると自動的にバックエンドが再起動
- ✅ 開発が効率的
- ⚠️ `PYTHONPATH`の設定が**必須**

リロードなしで起動する場合（`PYTHONPATH`不要）：
```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

## 🔧 トラブルシューティング

### すべてのプロセスを停止

```bash
pkill -9 -f uvicorn
```

### キャッシュをクリア

```bash
cd ~/batfish_vis/backend
find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find src -type f -name '*.pyc' -delete 2>/dev/null
```

### ファイルの存在確認

```bash
ls -la ~/batfish_vis/backend/src/__init__.py
ls -la ~/batfish_vis/backend/src/exceptions.py
find ~/batfish_vis/backend/src -name '__init__.py' | sort
```

### インポートテスト

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
PYTHONPATH=$PWD python -c 'from src.main import app; print("OK")'
```

## 📊 修正した問題の完全なリスト（8つ）

1. ✅ pybatfish APIの変更 (`bfq` → `session.q`)
2. ✅ exceptions.pyが存在しない → 作成・同期
3. ✅ Batfishバージョンが"unknown" → HTTP endpoint使用
4. ✅ **422 Unprocessable Entity** → FormData Content-Type修正
5. ✅ ログハンドラーKeyError (`msg`) → `error_msg`にリネーム
6. ✅ ログハンドラーKeyError (`filename`) → `file_name`にリネーム
7. ✅ **init_snapshot() APIエラー** → 正しいパラメータに修正
8. ✅ **__init__.pyが欠けている** → 全5ファイル作成・同期

## 🎉 まとめ

**推奨起動方法**（WSL Ubuntuターミナルでコピペ）:

```bash
cd ~/batfish_vis/backend && source .venv/bin/activate && pkill -9 -f uvicorn 2>/dev/null; find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null && PYTHONPATH=$PWD uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

または、Windows PowerShellから：

```powershell
cd D:\batfish_vis
.\start_backend_wsl.ps1
```

---

**これでバックエンドが正常に起動し、スナップショット作成が完全に動作します！**
