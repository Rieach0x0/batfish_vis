# Windows → WSL ファイル同期手順

## 問題

Windows側で修正したファイルがWSL側に反映されていないため、`ModuleNotFoundError: No module named 'src.exceptions'` エラーが発生しています。

## 解決方法

### オプション1: Windows側からWSL側に最新ファイルをコピー

#### 1. WSL Ubuntuターミナルで実行

```bash
# バックエンドプロセスを停止（Ctrl+C）

# 既存のプロジェクトディレクトリをバックアップ（オプション）
mv ~/batfish_vis ~/batfish_vis.backup

# Windows側から最新のファイルをコピー
cp -r /mnt/d/batfish_vis ~/batfish_vis

# ディレクトリに移動
cd ~/batfish_vis/backend

# 所有権を変更
sudo chown -R $USER:$USER ~/batfish_vis

# exceptions.pyが存在することを確認
ls -la src/exceptions.py
# 期待される出力: -rw-r--r-- 1 k-kawabe k-kawabe <size> <date> src/exceptions.py
```

#### 2. 仮想環境を再作成（推奨）

```bash
# 既存の仮想環境を削除
rm -rf .venv

# Python 3.11で仮想環境を作成
uv venv --python python3.11

# 仮想環境をアクティベート
source .venv/bin/activate

# Pythonバージョン確認
python --version
# 出力: Python 3.11.x

# 依存パッケージをインストール
uv pip install -r requirements.txt
```

#### 3. exceptions.pyのインポートを確認

```bash
# Pythonでインポートテスト
python -c "from src.exceptions import BatfishException; print('✓ exceptions.py imported successfully')"
```

**期待される出力**:
```
✓ exceptions.py imported successfully
```

**エラーが出る場合**:
```
ModuleNotFoundError: No module named 'src.exceptions'
```
→ exceptions.pyがコピーされていません。上記手順を再度実行してください。

#### 4. バックエンドを起動

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**期待される出力**:
```
INFO:     Will watch for changes in these directories: ['/home/k-kawabe/batfish_vis/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 5. ヘルスチェック（別のWSLターミナル）

```bash
curl http://localhost:8000/api/health
```

**期待される出力**:
```json
{
  "status": "healthy",
  "batfishVersion": "2025.07.07",
  "apiVersion": "1.0.0"
}
```

---

### オプション2: 個別ファイルのみコピー（高速）

新規作成・更新されたファイルのみコピーする方法:

```bash
# WSL Ubuntuターミナルで実行

# exceptions.pyをコピー
cp /mnt/d/batfish_vis/backend/src/exceptions.py ~/batfish_vis/backend/src/

# pyproject.tomlをコピー（Python 3.11+の設定）
cp /mnt/d/batfish_vis/backend/pyproject.toml ~/batfish_vis/backend/

# error_handler.pyをコピー（更新版）
cp /mnt/d/batfish_vis/backend/src/middleware/error_handler.py ~/batfish_vis/backend/src/middleware/

# main.pyをコピー（更新版）
cp /mnt/d/batfish_vis/backend/src/main.py ~/batfish_vis/backend/src/

# topology_service.pyをコピー（pybatfish API更新版）
cp /mnt/d/batfish_vis/backend/src/services/topology_service.py ~/batfish_vis/backend/src/services/

# verification_service.pyをコピー（pybatfish API更新版）
cp /mnt/d/batfish_vis/backend/src/services/verification_service.py ~/batfish_vis/backend/src/services/

# 所有権を確認・変更
sudo chown -R $USER:$USER ~/batfish_vis/backend/src

# インポート確認
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c "from src.exceptions import BatfishException; print('✓ OK')"

# バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

### オプション3: WSL側で直接ファイルを作成（手動）

exceptions.pyをWSL側で直接作成する方法:

```bash
# WSL Ubuntuターミナルで実行
cd ~/batfish_vis/backend/src

# exceptions.pyを作成
cat > exceptions.py << 'EOF'
"""
Custom exceptions for Batfish visualization backend.

Provides structured exception handling for Batfish-related errors.
"""


class BatfishException(Exception):
    """
    Base exception for Batfish-related errors.

    Raised when Batfish operations fail, including:
    - Connection errors to Batfish service
    - Query execution failures
    - Snapshot initialization errors
    - Configuration parsing errors

    This exception is caught by the error handler middleware
    and converted to a structured JSON error response.
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize Batfish exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary of additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class SnapshotException(BatfishException):
    """
    Exception for snapshot-related operations.

    Raised when snapshot operations fail, such as:
    - Snapshot creation with invalid configurations
    - Snapshot not found
    - Snapshot deletion errors
    """

    pass


class TopologyException(BatfishException):
    """
    Exception for topology query operations.

    Raised when topology extraction fails, such as:
    - Failed to retrieve nodes
    - Failed to retrieve edges
    - Failed to retrieve interface properties
    """

    pass


class VerificationException(BatfishException):
    """
    Exception for verification query operations.

    Raised when verification queries fail, such as:
    - Reachability query errors
    - ACL verification errors
    - Routing table query errors
    """

    pass


class FileUploadException(Exception):
    """
    Exception for file upload operations.

    Raised when file upload operations fail, such as:
    - Invalid file format
    - File size limit exceeded
    - File sanitization errors
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize file upload exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary of additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message
EOF

# ファイルが作成されたことを確認
ls -la exceptions.py
cat exceptions.py | head -20

# インポート確認
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c "from src.exceptions import BatfishException; print('✓ exceptions.py created successfully')"
```

---

## トラブルシューティング

### 問題1: cpコマンドで「Permission denied」

```bash
# 解決方法: sudoを使用
sudo cp /mnt/d/batfish_vis/backend/src/exceptions.py ~/batfish_vis/backend/src/

# 所有権を変更
sudo chown $USER:$USER ~/batfish_vis/backend/src/exceptions.py
```

### 問題2: /mnt/d/がマウントされていない

```bash
# Windows側のDドライブが見えるか確認
ls /mnt/d/

# 見えない場合、WSLを再起動
# Windows PowerShellで実行:
# wsl --shutdown
# wsl
```

### 問題3: インポートエラーが続く

```bash
# Pythonのキャッシュをクリア
cd ~/batfish_vis/backend
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 仮想環境を再作成
rm -rf .venv
uv venv --python python3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# インポート確認
python -c "from src.exceptions import BatfishException; print('✓ OK')"
```

---

## 推奨ワークフロー

今後、Windows側でファイルを修正した場合:

### 方法A: 完全同期（確実だが遅い）

```bash
# バックエンドを停止（Ctrl+C）

# プロジェクト全体を再同期
rm -rf ~/batfish_vis
cp -r /mnt/d/batfish_vis ~/batfish_vis
cd ~/batfish_vis/backend

# 仮想環境を再作成
rm -rf .venv
uv venv --python python3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# 起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 方法B: 差分同期（高速）

```bash
# 修正したファイルのみコピー
cp /mnt/d/batfish_vis/backend/src/<修正ファイル> ~/batfish_vis/backend/src/

# uvicornのauto-reloadが検知して自動再起動
# （--reloadオプションを使用している場合）
```

### 方法C: WSL側で直接開発（最速）

```bash
# VSCodeのRemote-WSL拡張機能を使用
# WSLターミナルで:
cd ~/batfish_vis/backend
code .

# VSCodeがWSL内で起動し、直接編集可能
# ファイル同期の問題が発生しない
```

---

## 確認コマンド集

```bash
# exceptions.pyの存在確認
ls -la ~/batfish_vis/backend/src/exceptions.py

# exceptions.pyの内容確認（最初の30行）
head -30 ~/batfish_vis/backend/src/exceptions.py

# Pythonインポート確認
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c "from src.exceptions import BatfishException; print('✓ OK')"

# すべての修正ファイルの存在確認
cd ~/batfish_vis/backend
echo "=== exceptions.py ===" && ls -la src/exceptions.py
echo "=== pyproject.toml ===" && ls -la pyproject.toml
echo "=== error_handler.py ===" && ls -la src/middleware/error_handler.py
echo "=== main.py ===" && ls -la src/main.py
echo "=== topology_service.py ===" && ls -la src/services/topology_service.py
echo "=== verification_service.py ===" && ls -la src/services/verification_service.py
```

---

## まとめ

**最も確実な方法**: オプション1（完全コピー）

```bash
# 1. プロジェクト全体をコピー
rm -rf ~/batfish_vis
cp -r /mnt/d/batfish_vis ~/batfish_vis
cd ~/batfish_vis/backend

# 2. 仮想環境を再作成
rm -rf .venv
uv venv --python python3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# 3. インポート確認
python -c "from src.exceptions import BatfishException; print('✓ OK')"

# 4. バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 5. ヘルスチェック（別ターミナル）
curl http://localhost:8000/api/health
```

これで確実にWindows側の最新ファイルがWSL側に反映されます。
