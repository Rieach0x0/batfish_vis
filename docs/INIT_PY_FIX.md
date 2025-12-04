# __init__.py修正 - Pythonパッケージ構造の修正

## 問題

バックエンドが起動時に以下のエラーで失敗：

```
ModuleNotFoundError: No module named 'src.exceptions'
```

## 根本原因

Pythonパッケージとして認識されるために必要な`__init__.py`ファイルが欠けていました。

### 欠けていたファイル

- `backend/src/__init__.py` ← **最も重要！**
- `backend/src/services/__init__.py`
- `backend/src/models/__init__.py`
- `backend/src/middleware/__init__.py`
- `backend/src/utils/__init__.py`

### 存在していたファイル

- `backend/src/api/__init__.py` ← これだけ存在

## 修正内容

すべての必要な`__init__.py`ファイルを作成してWSLに同期しました。

### 作成したファイル

1. **backend/src/__init__.py**
   ```python
   """
   Batfish Visualization Backend.

   Main package for the Batfish network visualization backend service.
   """

   __version__ = "1.0.0"
   ```

2. **backend/src/services/__init__.py**
   ```python
   """
   Services module for Batfish integration and business logic.
   """
   ```

3. **backend/src/models/__init__.py**
   ```python
   """
   Data models and schemas.
   """
   ```

4. **backend/src/middleware/__init__.py**
   ```python
   """
   Middleware for request/response processing.
   """
   ```

5. **backend/src/utils/__init__.py**
   ```python
   """
   Utility functions and helpers.
   """
   ```

## 確認方法

### WSL Ubuntuで以下のコマンドを実行：

```bash
# すべての__init__.pyファイルを確認
find ~/batfish_vis/backend/src -name '__init__.py' -type f | sort
```

### 期待される出力：

```
/home/k-kawabe/batfish_vis/backend/src/__init__.py
/home/k-kawabe/batfish_vis/backend/src/api/__init__.py
/home/k-kawabe/batfish_vis/backend/src/middleware/__init__.py
/home/k-kawabe/batfish_vis/backend/src/models/__init__.py
/home/k-kawabe/batfish_vis/backend/src/services/__init__.py
/home/k-kawabe/batfish_vis/backend/src/utils/__init__.py
```

### インポートテスト：

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c 'from src.main import app; print("Import successful!")'
```

✅ **成功すると**: `Import successful!` が表示される

## バックエンド再起動手順

### WSL Ubuntuターミナルで：

```bash
# ステップ1: 既存プロセスを停止（Ctrl+Cまたは）
pkill -f 'uvicorn src.main:app'

# ステップ2: バックエンドを再起動
cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 期待される起動ログ：

```
INFO:     Will watch for changes in these directories: ['/home/k-kawabe/batfish_vis/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
{"asctime": "...", "levelname": "INFO", "name": "root", "message": "Structured logging initialized", "log_level": "DEBUG"}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "CORS middleware configured", ...}
{"asctime": "...", "levelname": "INFO", "name": "src.main", "message": "FastAPI application initialized", ...}
INFO:     Application startup complete.
```

**重要**: `Application startup complete.` が表示されれば成功！

## Pythonパッケージの仕組み

### なぜ__init__.pyが必要か？

Pythonでは、ディレクトリをパッケージとして認識させるために`__init__.py`ファイルが必要です。

**なしの場合**:
```python
from src.exceptions import BatfishException
# ModuleNotFoundError: No module named 'src.exceptions'
```

**ありの場合**:
```python
from src.exceptions import BatfishException
# ✅ 正常にインポート
```

### ディレクトリ構造（修正後）

```
backend/
└── src/
    ├── __init__.py          ← 追加！
    ├── main.py
    ├── exceptions.py
    ├── api/
    │   ├── __init__.py      ← 既存
    │   └── snapshot_api.py
    ├── services/
    │   ├── __init__.py      ← 追加！
    │   ├── snapshot_service.py
    │   └── ...
    ├── models/
    │   ├── __init__.py      ← 追加！
    │   └── ...
    ├── middleware/
    │   ├── __init__.py      ← 追加！
    │   └── ...
    └── utils/
        ├── __init__.py      ← 追加！
        └── ...
```

## トラブルシューティング

### まだModuleNotFoundErrorが出る場合

```bash
# Pythonパスを確認
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c "import sys; print('\n'.join(sys.path))"

# __init__.pyが存在するか確認
ls -la ~/batfish_vis/backend/src/__init__.py
```

### __pycache__をクリアする

```bash
# 古いキャッシュを削除
find ~/batfish_vis/backend/src -type d -name '__pycache__' -exec rm -rf {} +
```

### 再度インポートテスト

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c 'from src.exceptions import BatfishException; print("OK!")'
```

## 全修正のまとめ

### 修正した問題（合計8つ）

1. ✅ pybatfish APIの変更 (`bfq` → `session.q`)
2. ✅ exceptions.pyが存在しない → 作成してWSLに同期
3. ✅ Batfishバージョンが"unknown" → HTTP endpoint使用
4. ✅ **422 Unprocessable Entity** → FormData Content-Type修正
5. ✅ ログハンドラーKeyError (`msg`) → `error_msg`にリネーム
6. ✅ ログハンドラーKeyError (`filename`) → `file_name`にリネーム (2箇所)
7. ✅ **init_snapshot() APIエラー** → 正しいパラメータ名に修正
8. ✅ **__init__.pyが欠けている** → 全5ファイル作成・同期 ← 今回

### 同期済みファイル（合計13ファイル）

#### Pythonコード (8ファイル)
- `backend/src/exceptions.py`
- `backend/src/main.py`
- `backend/src/api/snapshot_api.py`
- `backend/src/services/snapshot_service.py`
- `backend/src/services/file_service.py`
- `backend/src/services/batfish_service.py`
- `backend/src/services/topology_service.py`
- `backend/src/services/verification_service.py`

#### __init__.pyファイル (5ファイル)
- `backend/src/__init__.py` ← **重要！**
- `backend/src/services/__init__.py`
- `backend/src/models/__init__.py`
- `backend/src/middleware/__init__.py`
- `backend/src/utils/__init__.py`

## 次のステップ

1. **WSL Ubuntuターミナル**でバックエンドを再起動
2. `Application startup complete.` が表示されることを確認
3. ブラウザで http://localhost:5173 を開く
4. スナップショット作成をテスト

---

これで、すべての問題が解決し、バックエンドが正常に起動するはずです！
