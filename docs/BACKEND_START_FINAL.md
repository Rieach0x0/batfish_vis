# バックエンド起動手順 - 最終版

## 問題の診断結果

### 確認済み事項

✅ すべての`__init__.py`ファイルが存在
✅ `exceptions.py`が存在し、正しく同期されている
✅ Pythonから直接実行すると`from src.main import app`が成功
✅ すべてのインポートが正常に動作

### 問題の原因

uvicornの`--reload`オプションを使用すると、サブプロセスで起動するため、Pythonのインポートパスが正しく設定されない場合があります。

## 解決方法

### 方法1: リロードなしで起動（推奨）

開発中は、ファイルを変更するたびに手動で再起動します。

**WSL Ubuntuターミナル**で：

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate

# キャッシュをクリア
find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null

# リロードなしで起動
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

### 方法2: PYTHONPATHを設定してリロードを使用

環境変数を設定してからリロード機能を使用します。

**WSL Ubuntuターミナル**で：

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate

# キャッシュをクリア
find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null

# PYTHONPATHを設定して起動
PYTHONPATH=/home/k-kawabe/batfish_vis/backend uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 方法3: スタートアップスクリプトを使用（最も確実）

提供されているスクリプトを使用します。

**WSL Ubuntuターミナル**で：

```bash
cd ~/batfish_vis/backend
./start_backend.sh
```

## 起動成功の確認

### 期待される出力

```
INFO:     Will watch for changes in these directories: ['/home/k-kawabe/batfish_vis/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
{"asctime": "...", "levelname": "INFO", "name": "root", "message": "Structured logging initialized", "log_level": "DEBUG"}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "CORS middleware configured", "allowed_origins": ["http://localhost:5173", "http://localhost:3000"]}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "Exception handlers registered"}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "FastAPI application initialized", "title": "Batfish Visualization & Verification API", "version": "1.0.0", "batfish_host": "localhost", "batfish_port": 9996}
INFO:     Application startup complete.
```

**最重要**: `Application startup complete.` が表示されること！

### エラーが出る場合

#### ModuleNotFoundError: No module named 'src.exceptions'

```bash
# 手動でインポートテスト
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c 'from src.main import app; print("OK")'
```

成功する場合は、**方法2**（PYTHONPATH設定）または**方法3**（スクリプト使用）を試してください。

#### Port 8000 already in use

```bash
# 既存のプロセスを停止
pkill -9 -f uvicorn
```

#### Cannot connect to Batfish

```bash
# Batfishコンテナを確認
docker ps | grep batfish

# 起動していない場合
cd ~/batfish_vis
docker compose up -d
```

## ファイル変更後の再起動

### 方法1を使用している場合

```bash
# ターミナルでCtrl+Cを押して停止
# 再度起動
cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

### 方法2または3を使用している場合

ファイルを保存すると自動的にリロードされます。ターミナルに以下のメッセージが表示されます：

```
INFO:     Detected file change in '/home/k-kawabe/batfish_vis/backend/src/...'. Reloading...
```

## スナップショット作成テスト

バックエンドが起動したら：

### 1. ブラウザでフロントエンドを開く

http://localhost:5173

### 2. ヘルスチェック

画面上部に緑の "Connected to Batfish" が表示されることを確認

### 3. スナップショット作成

1. **Select Files** または **Select Folder** を選択
2. `.cfg` ファイルを選択（または `D:\networks\example` フォルダ）
3. Snapshot Name: `test-backend-fixed`
4. Network Name: `default`
5. **Create Snapshot** をクリック

### 期待される成功メッセージ

```
Snapshot "test-backend-fixed" created successfully! Detected 13 devices.
```

### バックエンドログの確認（WSLターミナル）

成功すると以下のようなログが表示されます：

```json
{"asctime": "...", "levelname": "INFO", "name": "src.api.snapshot_api", "message": "Snapshot creation request received", "snapshot": "test-backend-fixed", "network": "default", "file_count": 13}
{"asctime": "...", "levelname": "DEBUG", "name": "src.api.snapshot_api", "message": "File 1", "file_name": "as1border1.cfg", "content_type": "text/plain", "file_size": 3706}
...
{"asctime": "...", "levelname": "INFO", "name": "src.services.file_service", "message": "All files saved successfully", "snapshot": "test-backend-fixed", "files_saved": 13}
{"asctime": "...", "levelname": "INFO", "name": "src.services.snapshot_service", "message": "Creating Batfish snapshot", "snapshot": "test-backend-fixed", "network": "default"}
{"asctime": "...", "levelname": "INFO", "name": "src.services.snapshot_service", "message": "Batfish snapshot initialized", "snapshot": "test-backend-fixed", "network": "default"}
{"asctime": "...", "levelname": "INFO", "name": "src.services.snapshot_service", "message": "Snapshot created successfully", "snapshot": "test-backend-fixed", "device_count": 13, "parse_error_count": 0}
```

## トラブルシューティング

### キャッシュのクリア

```bash
cd ~/batfish_vis/backend
find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find src -type f -name '*.pyc' -delete 2>/dev/null
```

### すべてのプロセスを停止

```bash
pkill -9 -f uvicorn
```

### ファイルの存在確認

```bash
ls -la ~/batfish_vis/backend/src/__init__.py
ls -la ~/batfish_vis/backend/src/exceptions.py
ls -la ~/batfish_vis/backend/src/services/__init__.py
find ~/batfish_vis/backend/src -name '__init__.py' -type f
```

### インポートテスト

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c 'from src.main import app; print("SUCCESS")'
```

## クイックスタート（推奨コマンド）

**WSL Ubuntuターミナル**で以下をコピー＆ペースト：

```bash
# バックエンドディレクトリへ移動
cd ~/batfish_vis/backend

# 既存プロセスを停止
pkill -9 -f uvicorn 2>/dev/null

# キャッシュをクリア
find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null

# 仮想環境を有効化
source .venv/bin/activate

# バックエンドを起動（リロードなし - 最も安定）
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

または、リロード機能が必要な場合：

```bash
# バックエンドディレクトリへ移動
cd ~/batfish_vis/backend

# 既存プロセスを停止
pkill -9 -f uvicorn 2>/dev/null

# キャッシュをクリア
find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null

# 仮想環境を有効化
source .venv/bin/activate

# PYTHONPATHを設定してバックエンドを起動（リロード有効）
PYTHONPATH=$PWD uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

---

## まとめ

### 修正した問題（合計8つ）

1. ✅ pybatfish APIの変更
2. ✅ exceptions.pyが存在しない
3. ✅ Batfishバージョンが"unknown"
4. ✅ **422 Unprocessable Entity**
5. ✅ ログハンドラーKeyError (`msg`)
6. ✅ ログハンドラーKeyError (`filename`)
7. ✅ **init_snapshot() APIエラー**
8. ✅ **__init__.pyが欠けている**

### 同期済みファイル（合計13ファイル）

- Pythonコード: 8ファイル
- `__init__.py`: 5ファイル

**これで、バックエンドが正常に起動し、スナップショット作成が動作するはずです！**
