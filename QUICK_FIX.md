# 422エラー解決のためのクイックフィックス

## 現状の問題

1. フロントエンドとバックエンドは正常に動作している
2. 13個の.cfgファイルが正しく送信されている
3. しかし422エラーが発生している
4. **バックエンドの変更がWSLに反映されていない**ため、詳細なエラーログが出力されていない

## 最速の解決方法

### ステップ1: バックエンドの変更をWSLにコピー

#### Windows PowerShellで実行:

```powershell
# WSL Ubuntuが起動していることを確認
wsl echo "WSL is running"

# D:\batfish_vis\backend\src\main.py を WSLの ~/batfish_vis/backend/src/ にコピー
wsl cp /mnt/d/batfish_vis/backend/src/main.py ~/batfish_vis/backend/src/main.py

# コピーされたか確認
wsl cat ~/batfish_vis/backend/src/main.py | grep RequestValidationError
```

最後のコマンドで`RequestValidationError`が表示されればOKです。

### ステップ2: バックエンドを再起動

#### WSL Ubuntuターミナルで:

```bash
# 現在のバックエンドを停止（Ctrl+C）

cd ~/batfish_vis/backend
source .venv/bin/activate

# .envファイルを作成
cat > .env << 'EOF'
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=DEBUG
EOF

# バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### ステップ3: フロントエンドをリフレッシュ

#### Windows PowerShellで:

```powershell
# フロントエンドを停止（Ctrl+C）

cd D:\batfish_vis\frontend

# キャッシュクリア
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue

# 再起動
npm run dev
```

#### ブラウザで:

1. すべてのタブを閉じる
2. **Ctrl+Shift+Delete** でキャッシュクリア
3. ブラウザを再起動
4. http://localhost:5173 にアクセス

### ステップ4: 再度テスト

1. F12 → Console タブを開く
2. コンソールをクリア
3. **Select Files** を選択
4. `.cfg` ファイル**のみ**を13個選択
5. Snapshot Name: `test-config-only`
6. Create Snapshot をクリック

### ステップ5: ログを確認

#### A. ブラウザコンソール

正規表現の警告が**出なくなっている**ことを確認:
```
Pattern attribute value [a-zA-Z0-9_-]+ is not a valid regular expression
```
→ この警告が出なければ、フロントエンドの変更が反映されています。

422エラーが出た場合、以下のようなログが表示されるはず:
```
[VALIDATION ERROR] Full error object: { ... }
[VALIDATION ERROR] Details: [ ... ]
```

**このDetailsの内容をすべてコピーしてください。**

#### B. バックエンドログ（WSL Ubuntuターミナル）

422エラーが出た場合、以下のようなログが表示されるはず:
```
ERROR: Request validation error (422)
  url: http://localhost:8000/api/snapshots
  method: POST
  errors: [...]
ERROR: Validation error detail
  loc: ['body', 'configFiles']
  msg: field required
  type: value_error.missing
```

**このログをすべてコピーしてください。**

## 期待される結果

バックエンドとフロントエンドの変更が反映されれば、422エラーの**詳細な原因**が以下の2箇所に表示されます:

1. **ブラウザコンソール**: バックエンドから返された詳細なエラー情報
2. **バックエンドログ**: FastAPIのバリデーションエラー詳細

これにより、以下のいずれかが判明します:

### ケース1: `configFiles` フィールドが見つからない

```json
{
  "loc": ["body", "configFiles"],
  "msg": "field required",
  "type": "value_error.missing"
}
```

→ **原因**: FormDataの`configFiles`キーがバックエンドに到達していない
→ **対策**: Content-Typeやフォームフィールド名を確認

### ケース2: `snapshotName` のバリデーションエラー

```json
{
  "loc": ["body", "snapshotName"],
  "msg": "string does not match regex",
  "type": "value_error.str.regex"
}
```

→ **原因**: スナップショット名が正規表現パターンに一致していない
→ **対策**: バックエンドの正規表現を確認

### ケース3: ファイル数やサイズの問題

```json
{
  "loc": ["body", "configFiles"],
  "msg": "ensure this value has at least 1 items",
  "type": "value_error.list.min_items"
}
```

→ **原因**: ファイルが空または0個として認識されている
→ **対策**: FormDataの作成方法を確認

## もしまだエラーログが出ない場合

### オプション: curlで直接テスト

WSL Ubuntuターミナルで:

```bash
# バックエンドが起動している状態で、別のターミナルを開く

# テスト用ファイルを作成
echo "hostname test-router" > /tmp/test.cfg

# curlでPOSTリクエスト
curl -v -X POST http://localhost:8000/api/snapshots \
  -F "snapshotName=test-curl" \
  -F "networkName=default" \
  -F "configFiles=@/tmp/test.cfg"
```

**成功する場合**: バックエンドは正常で、フロントエンドに問題がある
**422エラーの場合**: バックエンドログに詳細なエラーが表示されるはず

## トラブルシューティング

### WSLへのコピーが失敗する場合

```powershell
# 手動でファイルを確認
wsl ls -la ~/batfish_vis/backend/src/

# main.pyが存在しない場合、ディレクトリを作成
wsl mkdir -p ~/batfish_vis/backend/src/

# 再度コピー
wsl cp /mnt/d/batfish_vis/backend/src/main.py ~/batfish_vis/backend/src/main.py
```

### uvicornが起動しない場合

```bash
# Pythonバージョンを確認
python3 --version  # 3.11以上が必要

# 仮想環境を再作成
cd ~/batfish_vis/backend
rm -rf .venv
uv venv --python python3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 次のステップ

上記のステップを実行して、以下の情報を報告してください:

1. **正規表現の警告が消えたか**: Yes / No
2. **ブラウザコンソールの[VALIDATION ERROR]ログ**: 全文コピー
3. **バックエンドの ERROR ログ**: 全文コピー
4. **curlテストの結果**: 成功 / 失敗（エラーメッセージ含む）

これにより、422エラーの正確な原因を特定できます。
