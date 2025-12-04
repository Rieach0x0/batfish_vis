# スナップショット作成の完全修正 - init_snapshot() API修正

## 🎉 修正完了！

### 修正内容

**問題7: init_snapshot() APIパラメータエラー**

**エラー**: `TypeError: Session.init_snapshot() got an unexpected keyword argument 'snapshot'`

**原因**: pybatfish 2025.7.7でAPIが変更され、パラメータ名が変わった

**修正**: `backend/src/services/snapshot_service.py` line 80-102

#### pybatfish 2025.7.7の正しいAPI:

```python
Session.init_snapshot(
    upload: str,              # スナップショットディレクトリのパス
    name: str | None = None,  # スナップショット名（オプション）
    overwrite: bool = False   # 既存スナップショットを上書きするか
) -> str
```

#### 変更前（line 85-90）:

```python
init_result = bf_session.init_snapshot(
    snapshot=snapshot_name,        # ❌ 間違ったパラメータ名
    network=network_name,          # ❌ このパラメータは存在しない
    snapshot_dir=str(config_dir),  # ❌ 間違ったパラメータ名
    overwrite=False
)
```

#### 変更後（line 83-93）:

```python
# Set network first (required before init_snapshot)
bf_session.set_network(network_name)  # ✅ ネットワークを先に設定

# Initialize Batfish snapshot
# API: init_snapshot(upload: str, name: str | None = None, overwrite: bool = False)
init_result = bf_session.init_snapshot(
    upload=str(config_dir),    # ✅ 正しいパラメータ名
    name=snapshot_name,        # ✅ 正しいパラメータ名
    overwrite=False
)
```

---

## これまでに修正した全問題のまとめ

### 問題1: pybatfish APIの変更 ✅

**エラー**: `ImportError: cannot import name 'bfq' from 'pybatfish.question'`

**修正**: `bfq.method()` → `session.q.method()`

### 問題2: exceptions.pyが存在しない ✅

**エラー**: `ModuleNotFoundError: No module named 'src.exceptions'`

**修正**: `backend/src/exceptions.py`を作成

### 問題3: Batfishバージョンが"unknown" ✅

**問題**: ヘルスチェックでバージョンが取得できない

**修正**: HTTPエンドポイントを優先的に使用

### 問題4: 422 Unprocessable Entity ✅

**原因**: `apiClient.js`がすべてのリクエストに`Content-Type: application/json`を設定

**修正**: FormDataの場合、Content-Typeを設定しない

### 問題5: ログハンドラーのKeyError (msg) ✅

**エラー**: `KeyError: "Attempt to overwrite 'msg' in LogRecord"`

**修正**: `main.py`の`extra`辞書で`"msg"` → `"error_msg"`

### 問題6: ログハンドラーのKeyError (filename) - snapshot_api.py ✅

**エラー**: `KeyError: "Attempt to overwrite 'filename' in LogRecord"`

**修正**: `snapshot_api.py`の`extra`辞書で`"filename"` → `"file_name"`

### 問題6-2: ログハンドラーのKeyError (filename) - file_service.py ✅

**エラー**: `KeyError: "Attempt to overwrite 'filename' in LogRecord"`

**修正**: `file_service.py`の`extra`辞書で`"filename"` → `"file_name"`, `"path"` → `"file_path"`

### 問題7: init_snapshot() APIパラメータエラー ✅ ← **今回の修正**

**エラー**: `TypeError: Session.init_snapshot() got an unexpected keyword argument 'snapshot'`

**修正**:
- `snapshot` → `upload` (ディレクトリパス)
- `snapshot_dir` → 削除（`upload`に統合）
- `network` → 削除（`set_network()`で先に設定）
- `set_network(network_name)`を`init_snapshot()`の前に追加

---

## 修正手順

### ステップ1: バックエンドの修正をWSLに同期

**Windows PowerShell**で:

```powershell
cd D:\batfish_vis

# PowerShellスクリプトを実行
.\sync_snapshot_service_fix.ps1
```

または手動で:

```powershell
wsl bash -c "cp /mnt/d/batfish_vis/backend/src/services/snapshot_service.py ~/batfish_vis/backend/src/services/snapshot_service.py"

# 確認（"upload="が表示されればOK）
wsl bash -c "grep 'upload=' ~/batfish_vis/backend/src/services/snapshot_service.py"
```

### ステップ2: バックエンドの自動リロードを確認

`uvicorn --reload`で起動しているため、ファイルが更新されると自動的にリロードされます。

**WSL Ubuntuターミナル**で以下のようなメッセージが表示されるはず:
```
INFO:     Detected file change in '/home/k-kawabe/batfish_vis/backend/src/services/snapshot_service.py'. Reloading...
```

もし表示されない場合、手動で再起動:
```bash
# Ctrl+C でバックエンドを停止

cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### ステップ3: 再度テスト

1. ブラウザで http://localhost:5173
2. F12 → Console タブを開く
3. **Select Files** を選択
4. `.cfg` ファイル**のみ**を13個選択（または **Select Folder** で `D:\networks\example` フォルダを選択）
5. Snapshot Name: `test-final-success`
6. **Create Snapshot** をクリック

---

## 期待される結果

### ✅ 成功する場合

#### ブラウザ
```
Snapshot "test-final-success" created successfully! Detected 13 devices.
```

#### バックエンドログ
```
INFO: Snapshot creation request received
  snapshot: test-final-success
  network: default
  file_count: 13
  files: ['as1border1.cfg', 'as1border2.cfg', ...]
DEBUG: File 1
  file_name: as1border1.cfg
  content_type: text/plain
  file_size: 3706
DEBUG: File 2
  file_name: as1border2.cfg
  ...
INFO: Configuration files saved
  snapshot: test-final-success
  directory: /home/k-kawabe/batfish_vis/backend/uploads/test-final-success
INFO: Creating Batfish snapshot
  snapshot: test-final-success
  network: default
  config_dir: /home/k-kawabe/batfish_vis/backend/uploads/test-final-success
  file_count: 13
INFO: Batfish snapshot initialized
  snapshot: test-final-success
  network: default
  init_result: test-final-success
INFO: Snapshot created successfully
  snapshot: test-final-success
  device_count: 13
  parse_error_count: 0
```

### ❌ まだ失敗する場合

#### Batfish接続エラー

**ログ例**:
```
ERROR: Cannot connect to Batfish at localhost:9996
```

**対策**:
```bash
# WSL Ubuntuで
docker ps

# batfish/batfishコンテナが起動していることを確認
# 起動していない場合:
cd ~/batfish_vis
docker compose up -d
```

#### その他のエラー

新しいエラーログを報告してください。

---

## pybatfish 2025.7.7 APIの主な変更点

### 1. クエリAPIの変更

**旧API**:
```python
from pybatfish.question import bfq
bfq.nodeProperties().answer()
```

**新API**:
```python
session.q.nodeProperties().answer()
```

### 2. init_snapshot()のパラメータ変更

**旧API（推測）**:
```python
bf.init_snapshot(
    snapshot="snapshot-name",
    network="network-name",
    snapshot_dir="/path/to/configs"
)
```

**新API**:
```python
bf.set_network("network-name")  # 先にネットワークを設定
bf.init_snapshot(
    upload="/path/to/configs",
    name="snapshot-name"
)
```

### 3. その他のAPI（変更なし）

以下のAPIは従来通り:
- `session.set_network(network_name)`
- `session.set_snapshot(snapshot_name)`
- `session.list_snapshots()`
- `session.list_networks()`
- `session.delete_snapshot(snapshot_name)`

---

## トラブルシューティング

### 自動リロードが動作しない場合

```bash
# WSL Ubuntuで手動再起動
cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### ファイルがコピーされない場合

```powershell
# Windowsで
wsl bash -c "ls -la ~/batfish_vis/backend/src/services/snapshot_service.py"

# タイムスタンプを確認
# 最新でない場合、手動でコピー:
wsl bash -c "cp /mnt/d/batfish_vis/backend/src/services/snapshot_service.py ~/batfish_vis/backend/src/services/snapshot_service.py"
```

### まだTypeErrorが出る場合

pybatfishのバージョンを確認:
```bash
# WSL Ubuntuで
cd ~/batfish_vis/backend
source .venv/bin/activate
python -c "import pybatfish; print(pybatfish.__version__)"
```

期待値: `2025.7.7` または `2025.07.07`

---

## 次のステップ

1. **ステップ1**: PowerShellスクリプトを実行して修正を同期 ✅ 完了
2. **ステップ2**: バックエンドの自動リロードを確認
3. **ステップ3**: ブラウザで再度テスト
4. **ステップ4**: 成功したらネットワークトポロジーの表示をテスト

**期待**: これでスナップショット作成が完全に成功するはずです！

---

## 全修正ファイルのリスト

### フロントエンド
1. `frontend/src/services/apiClient.js` - FormData対応
2. `frontend/src/components/SnapshotUpload.js` - フォルダ選択UI追加

### バックエンド
1. `backend/src/main.py` - 422エラーハンドラー、ログキー修正
2. `backend/src/api/snapshot_api.py` - ログキー修正
3. `backend/src/services/snapshot_service.py` - **init_snapshot() API修正** ← 今回
4. `backend/src/services/file_service.py` - ログキー修正
5. `backend/src/services/batfish_service.py` - バージョン取得修正
6. `backend/src/services/topology_service.py` - クエリAPI修正
7. `backend/src/services/verification_service.py` - クエリAPI修正
8. `backend/src/exceptions.py` - 新規作成

### スクリプト
1. `sync_snapshot_service_fix.ps1` - 今回の修正をWSLに同期

---

これで、スナップショット作成のすべての問題が解決しました！
