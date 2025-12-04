# 最終修正 - スナップショット作成の完全な解決

## 🎉 422エラーは解決しました！

### 進展の確認

**backend_error.log line 5**:
```json
{
  "message": "Snapshot creation request received",
  "snapshot": "test-config-only",
  "network": "default",
  "file_count": 13,
  "files": ["as1border1.cfg", "as1border2.cfg", "as1core1.cfg", ...]
}
```

**これは素晴らしいニュースです！**
- FormDataが正常にバックエンドに届いている ✅
- 13ファイルすべてが認識されている ✅
- snapshotNameとnetworkNameも正しく受信されている ✅

**422エラーは完全に解決しました！**

---

## 新しい問題: ログハンドラーのKeyError（500エラー）

### 問題

**backend_error.log line 6, 66**:
```
KeyError: "Attempt to overwrite 'filename' in LogRecord"
```

**原因**:
`snapshot_api.py` line 101 で`logger.debug()`の`extra`辞書に`"filename"`キーを使用していますが、これはPythonのlogging内部で予約されているキーです。

### 修正内容

**ファイル**: `backend/src/api/snapshot_api.py`

**変更前** (line 100-104):
```python
extra={
    "filename": file.filename,      # ← "filename"が衝突
    "content_type": file.content_type,
    "size": file.size if hasattr(file, 'size') else "unknown"
}
```

**変更後**:
```python
extra={
    "file_name": file.filename,     # ← "file_name"にリネーム
    "content_type": file.content_type,
    "file_size": file.size if hasattr(file, 'size') else "unknown"
}
```

---

## 修正手順

### ステップ1: バックエンドの修正をWSLに同期

**Windows PowerShell**で:

```powershell
cd D:\batfish_vis

# PowerShellスクリプトを実行
.\sync_snapshot_api_fix.ps1
```

または手動で:

```powershell
wsl bash -c "cp /mnt/d/batfish_vis/backend/src/api/snapshot_api.py ~/batfish_vis/backend/src/api/snapshot_api.py"

# 確認（"file_name"が表示されればOK）
wsl bash -c "grep 'file_name' ~/batfish_vis/backend/src/api/snapshot_api.py"
```

### ステップ2: バックエンドの自動リロードを確認

`uvicorn --reload`で起動しているため、ファイルが更新されると自動的にリロードされます。

**WSL Ubuntuターミナル**で以下のようなメッセージが表示されるはず:
```
INFO:     Detected file change in '/home/k-kawabe/batfish_vis/backend/src/api/snapshot_api.py'. Reloading...
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
4. `.cfg` ファイル**のみ**を13個選択
5. Snapshot Name: `test-success`
6. **Create Snapshot** をクリック

---

## 期待される結果

### ✅ 成功する場合

#### ブラウザ
```
Snapshot "test-success" created successfully! Detected 13 devices.
```

#### バックエンドログ
```
INFO: Snapshot creation request received
  snapshot: test-success
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
  snapshot: test-success
  directory: /tmp/...
INFO: Snapshot created successfully
  snapshot: test-success
  network: default
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

ログを報告してください。

---

## これまでに修正した問題のまとめ

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

### 問題6: ログハンドラーのKeyError (filename) ← **現在の問題**

**エラー**: `KeyError: "Attempt to overwrite 'filename' in LogRecord"`

**修正**: `snapshot_api.py`の`extra`辞書で`"filename"` → `"file_name"`

---

## Pythonのlogging予約キー

以下のキーは`logger.xxx()`の`extra`辞書で使用できません：

- `name`
- `msg`
- `args`
- `created`
- `msecs`
- `levelname`
- `levelno`
- `pathname`
- `filename` ← **今回の問題**
- `module`
- `lineno`
- `funcName`
- `process`
- `thread`
- `threadName`

**推奨**: これらのキーを避け、より具体的な名前を使用:
- `filename` → `file_name`, `uploaded_filename`, `config_filename`
- `msg` → `error_msg`, `warning_msg`, `info_msg`

---

## 次のステップ

1. **ステップ1**: PowerShellスクリプトを実行して修正を同期
2. **ステップ2**: バックエンドの自動リロードを確認
3. **ステップ3**: ブラウザで再度テスト
4. **ステップ4**: 結果を報告

**期待**: これでスナップショット作成が成功するはずです！

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
wsl bash -c "ls -la ~/batfish_vis/backend/src/api/snapshot_api.py"

# タイムスタンプを確認
# 最新でない場合、手動でコピー:
wsl bash -c "cp /mnt/d/batfish_vis/backend/src/api/snapshot_api.py ~/batfish_vis/backend/src/api/snapshot_api.py"
```

### まだKeyErrorが出る場合

別の予約キーを使用している可能性があります。エラーメッセージを報告してください。

---

これで、すべての問題が解決し、スナップショット作成が正常に動作するはずです！
