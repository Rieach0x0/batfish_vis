# バックエンドエラーの修正内容

## エラー概要

`log/backend_error.log` に記録されたバックエンド起動時のエラー:

1. **Python 3.10が使用されている**: Python 3.11+が必須だが、Python 3.10で実行されている
2. **pybatfishインポートエラー**: `ImportError: cannot import name 'bfq' from 'pybatfish.question'`

## 根本原因

### 1. Pythonバージョンの問題
- エラーログ: `/usr/lib/python3.10/...` パスが表示
- pyproject.tomlに `requires-python = ">=3.11"` が設定されていなかった
- uv venvでPythonバージョンを明示指定していなかった

### 2. pybatfish APIの変更
- pybatfish 2025.7.7以降で、クエリAPIが変更されました
- 旧: `from pybatfish.question import bfq` → `bfq.nodeProperties()`
- 新: `session.q.nodeProperties()` (Sessionオブジェクトから直接クエリを実行)

## 修正内容

### 1. pyproject.tomlの更新

**ファイル**: `backend/pyproject.toml`

```toml
[project]
name = "batfish-vis-backend"
version = "1.0.0"
description = "Batfish Visualization Backend API"
requires-python = ">=3.11"  # 追加: Python 3.11+を明示的に要求
```

これにより、uvがPython 3.11+をチェックし、警告を出すようになります。

### 2. topology_service.pyの修正

**ファイル**: `backend/src/services/topology_service.py`

**変更前**:
```python
from pybatfish.question import bfq

node_props = bfq.nodeProperties().answer().frame()
interface_props = bfq.interfaceProperties(nodes=hostname).answer().frame()
edges_df = bfq.layer3Edges().answer().frame()
```

**変更後**:
```python
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.flow import PathConstraints

def __init__(self, bf_session: Session):
    self.bf_session = bf_session
    self.bf = bf_session  # Alias for query methods

# クエリ実行時
node_props = self.bf.q.nodeProperties().answer().frame()
interface_props = self.bf.q.interfaceProperties(nodes=hostname).answer().frame()
edges_df = self.bf.q.layer3Edges().answer().frame()
```

### 3. verification_service.pyの修正

**ファイル**: `backend/src/services/verification_service.py`

**変更前**:
```python
from pybatfish.question import bfq
from pybatfish.datamodel.flow import HeaderConstraints

answer = bfq.reachability(headers=headers).answer()
answer = bfq.searchFilters(filters=filter_name, headers=headers).answer()
answer = bfq.routes(nodes=",".join(nodes)).answer()
```

**変更後**:
```python
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.flow import PathConstraints

def __init__(self, bf_session: Session):
    self.bf_session = bf_session
    self.bf = bf_session  # Alias for query methods

# クエリ実行時
answer = self.bf.q.reachability(headers=headers).answer()
answer = self.bf.q.searchFilters(filters=filter_name, headers=headers).answer()
answer = self.bf.q.routes(nodes=",".join(nodes)).answer()

# pathConstraintsの使用方法も変更
answer = self.bf.q.reachability(
    pathConstraints=PathConstraints(startLocation=src_node),
    headers=headers
).answer()
```

### 4. WSL_Ubuntu_Setup.mdの更新

**ファイル**: `docs/WSL_Ubuntu_Setup.md`

#### セクション2: Python環境セットアップ

**追加内容**:
```bash
# Python 3.11を明示的にインストール
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# python3をpython3.11にリンク（推奨）
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --config python3
```

#### セクション5: バックエンドAPI起動

**変更内容**:
```bash
# Python 3.11を明示的に指定
uv venv --python python3.11

# Pythonバージョン確認を追加
python --version
# 出力例: Python 3.11.7
```

#### セクション9: トラブルシューティング

**追加項目**:
- 9.5: Python 3.10が使用されている問題の解決方法
- 9.7: pybatfishのインポートエラーの説明

#### セクション10: 起動スクリプト

**変更内容**:
```bash
# Python 3.11を明示的に指定
uv venv --python python3.11
echo "Python version: $(python --version)"
```

## 修正後の動作確認手順

### 1. WSL Ubuntu環境のセットアップ

```bash
# Python 3.11をインストール
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Pythonバージョン確認
python3.11 --version
# 出力: Python 3.11.7

# uvをインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 2. プロジェクトをWSLにコピー

```bash
# 既存のプロジェクトディレクトリを削除
rm -rf ~/batfish_vis

# Windows側から最新のコードをコピー
cp -r /mnt/d/batfish_vis ~/batfish_vis
cd ~/batfish_vis/backend
```

### 3. Python環境を再構築

```bash
# 既存の仮想環境を削除
rm -rf .venv

# Python 3.11で仮想環境を作成
uv venv --python python3.11

# 仮想環境をアクティベート
source .venv/bin/activate

# Pythonバージョン確認（必須）
python --version
# 期待される出力: Python 3.11.7

# 依存パッケージをインストール
uv pip install -r requirements.txt
```

### 4. バックエンドAPIを起動

```bash
# 起動
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
- `ImportError: cannot import name 'bfq'` が出ないこと
- `python3.10` のパスが表示されないこと
- 正常に起動すること

### 5. ヘルスチェック

別のターミナルで:
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

## pybatfish API変更の詳細

### 旧API (pybatfish < 2025.7.7)

```python
from pybatfish.question import bfq

# グローバルなbfqオブジェクトを使用
node_props = bfq.nodeProperties().answer().frame()
```

### 新API (pybatfish >= 2025.7.7)

```python
from pybatfish.client.session import Session

bf = Session(host="localhost")
bf.set_network("default")
bf.set_snapshot("my-snapshot")

# Sessionオブジェクトのqプロパティを使用
node_props = bf.q.nodeProperties().answer().frame()
```

### 変更された主なクエリメソッド

| 旧API | 新API |
|-------|-------|
| `bfq.nodeProperties()` | `bf.q.nodeProperties()` |
| `bfq.interfaceProperties()` | `bf.q.interfaceProperties()` |
| `bfq.layer3Edges()` | `bf.q.layer3Edges()` |
| `bfq.reachability()` | `bf.q.reachability()` |
| `bfq.searchFilters()` | `bf.q.searchFilters()` |
| `bfq.routes()` | `bf.q.routes()` |

### pathConstraintsの変更

**旧API**:
```python
bfq.reachability(
    pathConstraints={"startLocation": src_node},
    headers=headers
)
```

**新API**:
```python
from pybatfish.datamodel.flow import PathConstraints

bf.q.reachability(
    pathConstraints=PathConstraints(startLocation=src_node),
    headers=headers
)
```

## まとめ

修正内容:
1. ✅ **pyproject.toml**: `requires-python = ">=3.11"` を追加
2. ✅ **topology_service.py**: `bfq` → `self.bf.q` に変更
3. ✅ **verification_service.py**: `bfq` → `self.bf.q` に変更、`PathConstraints`の使用
4. ✅ **WSL_Ubuntu_Setup.md**: Python 3.11のインストール手順を追加、トラブルシューティングを拡充

これらの修正により:
- Python 3.11+が確実に使用される
- pybatfish 2025.7.7の新しいAPIに対応
- エラーなくバックエンドが起動する
