# バックエンド再起動手順

## 問題

バックエンドが `ModuleNotFoundError: No module named 'src.exceptions'` で起動に失敗していました。

## 修正内容

すべてのバックエンド修正ファイルをWSLに同期しました：

✅ `backend/src/exceptions.py` - 新規作成（エラー定義）
✅ `backend/src/main.py` - 422エラーハンドラー、ログキー修正
✅ `backend/src/api/snapshot_api.py` - ログキー修正
✅ `backend/src/services/snapshot_service.py` - **init_snapshot() API修正**
✅ `backend/src/services/file_service.py` - ログキー修正
✅ `backend/src/services/batfish_service.py` - バージョン取得修正
✅ `backend/src/services/topology_service.py` - クエリAPI修正
✅ `backend/src/services/verification_service.py` - クエリAPI修正

## バックエンド再起動手順

### ステップ1: WSL Ubuntuターミナルを開く

Windows Terminal または WSL Ubuntu ターミナルを開いてください。

### ステップ2: 既存のバックエンドプロセスを停止

現在のバックエンドプロセスを停止します：

```bash
# 現在実行中のuvicornプロセスを確認
pgrep -f 'uvicorn src.main:app'

# プロセスを停止（Ctrl+Cが効かない場合）
pkill -f 'uvicorn src.main:app'

# 停止を確認（何も表示されなければOK）
pgrep -f 'uvicorn src.main:app'
```

または、uvicornが実行中のターミナルで **Ctrl+C** を押してください。

### ステップ3: バックエンドを再起動

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### ステップ4: 起動成功を確認

以下のようなメッセージが表示されれば成功です：

```
INFO:     Will watch for changes in these directories: ['/home/k-kawabe/batfish_vis/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**重要**: `Application startup complete.` が表示されるまで待ってください！

### ステップ5: エラーがないか確認

もし起動時にエラーが出た場合：

```bash
# エラーログを確認
tail -50 ~/batfish_vis/log/backend_error.log
```

エラーが出た場合は、そのログを報告してください。

## テスト手順

### 1. ブラウザでフロントエンドを開く

http://localhost:5173

### 2. ヘルスチェック

画面上部に緑の "Connected to Batfish" が表示されることを確認

### 3. スナップショット作成テスト

1. **Select Files** または **Select Folder** を選択
2. `.cfg` ファイルを選択（または `D:\networks\example` フォルダ）
3. Snapshot Name: `test-complete-fix`
4. Network Name: `default` （デフォルト）
5. **Create Snapshot** をクリック

### 期待される結果

✅ **成功メッセージ**:
```
Snapshot "test-complete-fix" created successfully! Detected 13 devices.
```

✅ **バックエンドログ**（WSLターミナル）:
```
INFO: Snapshot creation request received
  snapshot: test-complete-fix
  network: default
  file_count: 13
INFO: Configuration files saved
INFO: Creating Batfish snapshot
INFO: Batfish snapshot initialized
INFO: Snapshot created successfully
  device_count: 13
  parse_error_count: 0
```

## トラブルシューティング

### エラー: Port 8000 already in use

```bash
# ポート8000を使用しているプロセスを確認
lsof -i :8000

# プロセスを停止
pkill -f 'uvicorn src.main:app'
```

### エラー: Cannot connect to Batfish

```bash
# Batfishコンテナの状態を確認
docker ps

# batfish/batfishが起動していない場合
cd ~/batfish_vis
docker compose up -d

# ログを確認
docker logs batfish
```

### バックエンドログの確認方法

```bash
# リアルタイムでログを監視
tail -f ~/batfish_vis/log/backend_error.log

# 最新50行を表示
tail -50 ~/batfish_vis/log/backend_error.log
```

## 次のステップ

スナップショット作成が成功したら：

1. **Snapshots** タブでスナップショット一覧を確認
2. 作成したスナップショットを選択
3. **Topology** タブでネットワークトポロジーを表示
4. ノードやリンクにカーソルを当てて詳細情報を確認

---

## すべての修正のまとめ

### 修正した問題（合計7つ）

1. ✅ pybatfish APIの変更 (`bfq` → `session.q`)
2. ✅ exceptions.pyが存在しない → 作成してWSLに同期
3. ✅ Batfishバージョンが"unknown" → HTTP endpoint使用
4. ✅ **422 Unprocessable Entity** → FormData Content-Type修正
5. ✅ ログハンドラーKeyError (`msg`) → `error_msg`にリネーム
6. ✅ ログハンドラーKeyError (`filename`) → `file_name`にリネーム (2箇所)
7. ✅ **init_snapshot() APIエラー** → 正しいパラメータ名に修正

### 同期済みファイル（合計8ファイル）

- `backend/src/exceptions.py` ← **重要！これが欠けていた**
- `backend/src/main.py`
- `backend/src/api/snapshot_api.py`
- `backend/src/services/snapshot_service.py`
- `backend/src/services/file_service.py`
- `backend/src/services/batfish_service.py`
- `backend/src/services/topology_service.py`
- `backend/src/services/verification_service.py`

---

これで、バックエンドが正常に起動し、スナップショット作成が完全に動作するはずです！
