# バックエンドエラー修正 - 第2回

## エラー概要

`log/backend_error.log` の最新エラー:

```
ModuleNotFoundError: No module named 'src.exceptions'
```

**ファイル**: `backend/src/services/topology_service.py:19`

## 根本原因

`backend/src/exceptions.py` モジュールが存在しませんでした。

サービスレイヤー（topology_service.py、verification_service.py）では独自の`BatfishException`を使用する設計でしたが、`exceptions.py`ファイルが作成されていませんでした。

## 修正内容

### 1. exceptions.pyの作成

**ファイル**: `backend/src/exceptions.py` (新規作成)

カスタム例外クラスを定義:

```python
class BatfishException(Exception):
    """
    Base exception for Batfish-related errors.

    Raised when Batfish operations fail, including:
    - Connection errors to Batfish service
    - Query execution failures
    - Snapshot initialization errors
    - Configuration parsing errors
    """

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class SnapshotException(BatfishException):
    """Exception for snapshot-related operations."""
    pass

class TopologyException(BatfishException):
    """Exception for topology query operations."""
    pass

class VerificationException(BatfishException):
    """Exception for verification query operations."""
    pass

class FileUploadException(Exception):
    """Exception for file upload operations."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
```

### 2. error_handler.pyの更新

**ファイル**: `backend/src/middleware/error_handler.py`

**変更点**: 両方のBatfishException（独自版とpybatfish版）を処理できるように修正

**変更前**:
```python
from pybatfish.exception import BatfishException

async def batfish_exception_handler(request: Request, exc: BatfishException) -> JSONResponse:
```

**変更後**:
```python
from typing import Union
from pybatfish.exception import BatfishException as PyBatfishException
from ..exceptions import BatfishException

async def batfish_exception_handler(
    request: Request,
    exc: Union[BatfishException, PyBatfishException]
) -> JSONResponse:
```

### 3. main.pyの更新

**ファイル**: `backend/src/main.py`

**変更点**: 両方のBatfishExceptionを例外ハンドラーに登録

**変更前**:
```python
from pybatfish.exception import BatfishException

# Register exception handlers
app.add_exception_handler(BatfishException, batfish_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

**変更後**:
```python
from pybatfish.exception import BatfishException as PyBatfishException
from .exceptions import BatfishException

# Register exception handlers
# Handle both custom BatfishException and pybatfish's BatfishException
app.add_exception_handler(BatfishException, batfish_exception_handler)
app.add_exception_handler(PyBatfishException, batfish_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

## 例外クラスの使い分け

### 1. 独自のBatfishException (`src.exceptions.BatfishException`)

**使用場所**: サービスレイヤー（topology_service.py, verification_service.py）

**用途**:
- サービス層でのエラーハンドリング
- 詳細な情報（detailsフィールド）を含むエラー
- ビジネスロジックレベルのエラー

**例**:
```python
from ..exceptions import BatfishException

try:
    node_props = self.bf.q.nodeProperties().answer().frame()
except Exception as e:
    raise BatfishException(f"Failed to retrieve devices: {str(e)}")
```

### 2. pybatfishのBatfishException (`pybatfish.exception.BatfishException`)

**使用場所**: snapshot_service.py, または直接pybatfishから発生

**用途**:
- pybatfishライブラリが直接発生させるエラー
- Batfish接続エラー、通信エラー

**例**:
```python
from pybatfish.exception import BatfishException

try:
    self.bf.init_snapshot(snapshot_name, config_dir)
except BatfishException as e:
    # pybatfishが直接発生させたエラー
    logger.error(f"Snapshot initialization failed: {str(e)}")
    raise
```

### 3. 例外ハンドラーでの処理

両方の例外タイプを同じハンドラーで処理:

```python
async def batfish_exception_handler(
    request: Request,
    exc: Union[BatfishException, PyBatfishException]
) -> JSONResponse:
    # 両方の例外タイプを統一的に処理
    error_message = str(exc).lower()
    # ... トラブルシューティング情報の生成
```

## 例外階層

```
Exception (Python組み込み)
│
├── BatfishException (独自 - src.exceptions)
│   ├── SnapshotException
│   ├── TopologyException
│   └── VerificationException
│
├── BatfishException (pybatfish - pybatfish.exception)
│   └── (pybatfishが内部で使用)
│
└── FileUploadException (独自 - src.exceptions)
```

## 修正後の動作確認

### 1. Pythonモジュールのインポート確認

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate

# Pythonでインポートテスト
python -c "from src.exceptions import BatfishException; print('OK')"
# 出力: OK
```

### 2. バックエンドAPIを起動

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

**エラーが出ないこと**:
- `ModuleNotFoundError: No module named 'src.exceptions'` が出ないこと
- 正常に起動すること

### 3. ヘルスチェック

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

## ファイル構造

修正後のバックエンドディレクトリ構造:

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py                    # ✅ 更新: 両方のBatfishExceptionを登録
│   ├── config.py
│   ├── exceptions.py              # ✅ 新規作成
│   ├── api/
│   │   ├── __init__.py
│   │   ├── topology_api.py
│   │   ├── verification_api.py
│   │   └── snapshot_api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── batfish_service.py
│   │   ├── topology_service.py    # → 独自BatfishExceptionを使用
│   │   ├── verification_service.py # → 独自BatfishExceptionを使用
│   │   ├── snapshot_service.py    # → pybatfish BatfishExceptionを使用
│   │   └── file_service.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── error_handler.py       # ✅ 更新: 両方の例外を処理
│   ├── models/
│   └── utils/
├── pyproject.toml
└── requirements.txt
```

## まとめ

### 修正内容
1. ✅ `src/exceptions.py` を新規作成
   - `BatfishException` (基底クラス)
   - `SnapshotException`, `TopologyException`, `VerificationException` (派生クラス)
   - `FileUploadException`

2. ✅ `src/middleware/error_handler.py` を更新
   - 独自版とpybatfish版の両方を処理できるように型ヒントを追加
   - `Union[BatfishException, PyBatfishException]`

3. ✅ `src/main.py` を更新
   - 両方のBatfishExceptionを例外ハンドラーに登録
   - `app.add_exception_handler(BatfishException, ...)` (独自版)
   - `app.add_exception_handler(PyBatfishException, ...)` (pybatfish版)

### これにより
- モジュールインポートエラーが解消
- サービスレイヤーでの独自例外が使用可能
- pybatfishからの例外も適切にハンドリング
- エラーハンドリングの一貫性が向上

### 次のステップ

WSL Ubuntu上で以下を実行:

```bash
# バックエンドディレクトリに移動
cd ~/batfish_vis/backend

# 仮想環境をアクティベート
source .venv/bin/activate

# バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

正常に起動すれば修正完了です！
