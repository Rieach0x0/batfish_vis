# 422エラーの根本原因を発見

## エラーログ分析結果

### 重要な発見

#### 1. フロントエンドは正常にFormDataを作成している ✅

**frontend_error.log line 30-44**:
```
FormData entries:
  snapshotName: test-config-only
  networkName: default
  configFiles: File(as1border1.cfg, 3706 bytes)
  configFiles: File(as1border2.cfg, 3847 bytes)
  ... (13 files total)
```

→ フロントエンドは完全に正常です。

#### 2. バックエンドは空のFormDataを受信している ❌

**backend_error.log line 31**:
```json
{
  "errors": [
    {"type": "missing", "loc": ["body", "snapshotName"], "msg": "Field required"},
    {"type": "missing", "loc": ["body", "configFiles"], "msg": "Field required"}
  ],
  "body": "FormData([])"  ← 空！
}
```

→ バックエンドには何も届いていません。

#### 3. ログハンドラーにバグがある（500エラーの原因）

**backend_error.log line 32, 92**:
```
KeyError: "Attempt to overwrite 'msg' in LogRecord"
```

→ `logger.error()`の`extra`辞書に`msg`キーが含まれており、Pythonのlogging内部の`msg`と衝突しています。

#### 4. 500エラーによりCORSヘッダーが返されない

**frontend_error.log line 47-48**:
```
Access to fetch at 'http://localhost:8000/api/snapshots' from origin 'http://localhost:5173'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
POST http://localhost:8000/api/snapshots net::ERR_FAILED 500 (Internal Server Error)
```

→ 500エラーの場合、FastAPIはCORSヘッダーを返さないため、ブラウザがブロックします。

## 問題の流れ

```
1. フロントエンド
   ↓ FormDataを正しく作成（snapshotName + 13 files）
   ↓ POST http://localhost:8000/api/snapshots

2. ネットワーク
   ↓ multipart/form-data として送信

3. バックエンド（FastAPI）
   ↓ multipart/form-dataをパース
   ↓ ❌ パース失敗？または空のFormDataとして解釈？
   ↓ RequestValidationError発生（422エラー）
   ↓ validation_exception_handler実行
   ↓ ❌ logger.error()でKeyError発生（500エラー）
   ↓ 500エラーを返す（CORSヘッダーなし）

4. ブラウザ
   ↓ CORSヘッダーがないためブロック
   ↓ "Network error" としてフロントエンドに通知
```

## 修正内容

### 修正1: ログハンドラーのバグを修正 ✅

**ファイル**: `backend/src/main.py`

**変更前**:
```python
for error in exc.errors():
    logger.error(
        f"Validation error detail",
        extra={
            "loc": error.get("loc"),
            "msg": error.get("msg"),      # ← "msg"が衝突
            "type": error.get("type"),
            "input": error.get("input")
        }
    )
```

**変更後**:
```python
for error in exc.errors():
    logger.error(
        f"Validation error detail",
        extra={
            "field_loc": error.get("loc"),
            "error_msg": error.get("msg"),     # ← "error_msg"にリネーム
            "error_type": error.get("type"),
            "error_input": error.get("input")
        }
    )
```

これにより、500エラーは解消され、422エラーの詳細が正しくログ出力されるようになります。

## 次のステップ

### ステップ1: 修正をWSLに同期

**Windows PowerShell**で:

```powershell
# sync_backend_fix.ps1を実行
cd D:\batfish_vis
.\sync_backend_fix.ps1
```

または手動で:

```powershell
wsl bash -c "cp /mnt/d/batfish_vis/backend/src/main.py ~/batfish_vis/backend/src/main.py"
wsl bash -c "grep -n 'error_msg' ~/batfish_vis/backend/src/main.py"
```

最後のコマンドで`error_msg`が表示されればOKです。

### ステップ2: バックエンドを再起動

**WSL Ubuntuターミナル**で:

```bash
# Ctrl+C でバックエンドを停止

cd ~/batfish_vis/backend
source .venv/bin/activate

# 再起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### ステップ3: 再度テスト

1. ブラウザで http://localhost:5173 にアクセス
2. F12 → Console タブを開く
3. コンソールをクリア
4. **Select Files** を選択
5. `.cfg` ファイル**のみ**を13個選択
6. Snapshot Name: `test-config-only`
7. **Create Snapshot** をクリック

### ステップ4: ログを確認

#### A. バックエンドログ（WSL Ubuntuターミナル）

**期待されるログ（500エラーが出なくなる）**:

```
ERROR: Request validation error (422)
  url: http://localhost:8000/api/snapshots
  method: POST
  errors: [...]
  body: ...
ERROR: Validation error detail
  field_loc: ['body', 'snapshotName']
  error_msg: Field required
  error_type: missing
```

**重要**: `body:` の部分に何が表示されるか確認してください。

- `body: "FormData([])"`  → まだ空（別の問題がある）
- `body: <multipart form data>` → FormDataは届いているが、パースに失敗している

#### B. ブラウザコンソール

**期待される変化**:

- CORSエラーが出なくなる
- 422エラーの詳細が表示される

```
[VALIDATION ERROR] Full error object: { ... }
[VALIDATION ERROR] Details: [ ... ]
```

**このDetailsの内容をすべてコピーして報告してください。**

## 予想される次の問題

### シナリオ1: まだ `body: "FormData([])"`（空）

**原因の可能性**:
1. FastAPIの`multipart/form-data`パーサーがファイルを認識していない
2. Content-Typeヘッダーが正しく設定されていない
3. ブラウザがFormDataを正しく送信していない

**対策**:
- `apiClient.js`の`postForm`メソッドを確認
- Content-Typeヘッダーが手動で設定されていないか確認
- curlで直接テスト

### シナリオ2: `body:` に何かデータがあるが、パースエラー

**原因の可能性**:
1. フィールド名が一致していない（`configFiles` vs 他の名前）
2. FastAPIのForm/Fileパラメータ定義が間違っている
3. multipartのboundaryが正しくない

**対策**:
- バックエンドのログに表示された`body:`の内容を分析
- `snapshot_api.py`のパラメータ定義を確認

### シナリオ3: 成功する

おめでとうございます！422エラーは解決しました。

## 暫定的な対応策

もし、上記の修正でもFormDataが空のまま届く場合は、以下の暫定対応を検討してください:

### オプション1: curlで直接テスト

バックエンドが正常かどうかを確認:

```bash
# WSL Ubuntuで
cd ~/batfish_vis/backend

# テスト用ファイルを作成
echo "hostname test-router" > /tmp/test.cfg

# curlでPOST
curl -v -X POST http://localhost:8000/api/snapshots \
  -F "snapshotName=test-curl" \
  -F "networkName=default" \
  -F "configFiles=@/tmp/test.cfg"
```

**成功する場合**: バックエンドは正常で、フロントエンドのFormData送信に問題がある
**失敗する場合**: バックエンドのmultipart処理に問題がある

### オプション2: Content-Typeの確認

`apiClient.js`のpostFormメソッドで、Content-Typeが手動設定されていないか確認:

```javascript
// ❌ 悪い例（手動でContent-Type設定）
headers: {
  'Content-Type': 'multipart/form-data'  // これがあると動かない
}

// ✅ 良い例（ブラウザに任せる）
// headers: {} または headers省略
```

## まとめ

**確認されたこと**:
1. ✅ フロントエンドは正常に動作している
2. ✅ FormDataは正しく作成されている
3. ❌ バックエンドは空のFormDataを受信している
4. ❌ ログハンドラーにバグがあり、500エラーを引き起こしている

**修正したこと**:
1. ✅ ログハンドラーのKeyErrorを修正（`msg` → `error_msg`）

**次にやること**:
1. 修正をWSLに同期
2. バックエンドを再起動
3. 再度テストしてログを確認
4. `body:` の内容を報告

**最も重要な確認ポイント**:
- バックエンドログの `body:` に何が表示されるか
- FormDataが空のまま（`FormData([])`）か、何かデータがあるか

これにより、FormDataが送信段階で失われているのか、バックエンドのパース段階で失われているのかが判明します。
