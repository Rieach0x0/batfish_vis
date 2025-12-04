# 422 Unprocessable Entity エラーのトラブルシューティング

## エラー内容

**フロントエンド表示**:
```
Unprocessable Entity
```

**バックエンドログ**:
```
POST /api/snapshots HTTP/1.1" 422 Unprocessable Entity
```

## 422エラーの原因

FastAPIの422エラーは、リクエストのバリデーションに失敗したことを示します。

### 主な原因

1. **フォームデータのパラメータ名が不一致**
   - フロントエンド: `configFiles`
   - バックエンド期待値: `configFiles`
   - 不一致があると422エラー

2. **必須パラメータが欠落**
   - `snapshotName`: 必須
   - `configFiles`: 必須（最低1ファイル）
   - いずれかが欠けると422エラー

3. **ファイルが空または0バイト**
   - 空のFileオブジェクトが送信される
   - FastAPIが正しく処理できない

4. **Content-Typeが不正**
   - `multipart/form-data`である必要がある
   - 異なるContent-Typeは422エラー

## 診断手順

### ステップ1: バックエンドログレベルをDEBUGに設定

```bash
# WSL Ubuntuターミナルで
cd ~/batfish_vis/backend

# .envファイルを編集
cat > .env << EOF
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=DEBUG
EOF

# バックエンドを再起動
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### ステップ2: テスト用フォルダを作成

```bash
# Windowsで実行
mkdir D:\networks\example
echo hostname router1 > D:\networks\example\router1.cfg
echo hostname switch1 > D:\networks\example\switch1.cfg
```

### ステップ3: フロントエンドのブラウザコンソールを確認

1. ブラウザでF12キーを押してデベロッパーツールを開く
2. **Console**タブを開く
3. フォルダをアップロード
4. コンソールに以下のようなメッセージが表示されるか確認:

```javascript
Creating snapshot: test-snapshot with 2 files
```

もしファイル数が0の場合:
```javascript
Creating snapshot: test-snapshot with 0 files
```
→ **これが422エラーの原因**

### ステップ4: ネットワークタブでリクエストを確認

1. デベロッパーツールの**Network**タブを開く
2. フォルダをアップロード
3. `POST /api/snapshots`リクエストを選択
4. **Request**セクションを確認

**正常なリクエスト**:
```
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...

------WebKitFormBoundary...
Content-Disposition: form-data; name="snapshotName"

test-snapshot
------WebKitFormBoundary...
Content-Disposition: form-data; name="networkName"

default
------WebKitFormBoundary...
Content-Disposition: form-data; name="configFiles"; filename="router1.cfg"
Content-Type: text/plain

<file content>
------WebKitFormBoundary...
```

**異常なリクエスト（422の原因）**:
```
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...

------WebKitFormBoundary...
Content-Disposition: form-data; name="snapshotName"

test-snapshot
------WebKitFormBoundary...
Content-Disposition: form-data; name="networkName"

default
------WebKitFormBoundary...
(ファイルデータがない)
```

### ステップ5: バックエンドログを確認

バックエンドターミナルで以下のようなログが表示されるはず:

**正常な場合**:
```
INFO: Snapshot creation request received
  snapshot: test-snapshot
  network: default
  file_count: 2
  files: ['router1.cfg', 'switch1.cfg']
DEBUG: File 1
  filename: router1.cfg
  content_type: text/plain
```

**422エラーの場合（ログが表示されない）**:
FastAPIのバリデーションエラーで、エンドポイント関数が実行される前にエラーが発生します。

## 解決方法

### 解決方法1: ファイルモードで個別ファイルを選択

フォルダモードで問題が発生する場合、まず個別ファイル選択で動作確認:

1. フロントエンドで**Select Files**を選択
2. 「ファイルを選択」をクリック
3. `D:\networks\example`フォルダを開く
4. `Ctrl+A`ですべてのファイルを選択
5. 「開く」をクリック
6. スナップショットを作成

**これで成功する場合**: フォルダモードに問題がある

**これでも失敗する場合**: バックエンドまたはネットワークに問題がある

### 解決方法2: ブラウザキャッシュをクリア

1. Ctrl+Shift+Del (Chromeの場合)
2. 「キャッシュされた画像とファイル」を選択
3. 「データを削除」をクリック
4. ブラウザを再起動
5. 再度アップロードを試す

### 解決方法3: フロントエンドコードを更新

最新のSnapshotUpload.jsがWSLにコピーされているか確認:

```bash
# WSL Ubuntuターミナルで
cd ~/batfish_vis

# Windows側から最新ファイルをコピー
cp /mnt/d/batfish_vis/frontend/src/components/SnapshotUpload.js ~/batfish_vis/frontend/src/components/

# 所有権を変更
sudo chown $USER:$USER ~/batfish_vis/frontend/src/components/SnapshotUpload.js

# Windowsに戻ってフロントエンドを再起動
# Windows PowerShellで:
cd D:\batfish_vis\frontend
npm run dev
```

### 解決方法4: FastAPIのバリデーションエラーメッセージを確認

FastAPIの422エラーには詳細情報が含まれています。

**ブラウザのNetwork タブで確認**:

1. `POST /api/snapshots`リクエストを選択
2. **Response**タブを確認

**422エラーの詳細例**:
```json
{
  "detail": [
    {
      "loc": ["body", "configFiles"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

これは`configFiles`フィールドが欠落していることを示します。

### 解決方法5: 最小限のテストケース

最小限のファイルでテスト:

```bash
# 1つの小さなファイルを作成
echo "hostname test-router" > D:\networks\example\test.cfg
```

フロントエンドで:
1. **Select Files**モードを選択
2. `test.cfg`のみを選択
3. Snapshot Name: `test-minimal`
4. 「Create Snapshot」をクリック

**これで成功する場合**: ファイル数やサイズの問題

**これでも失敗する場合**: 基本的な設定に問題

## よくある問題と解決策

### 問題1: フォルダに設定ファイルがない

**症状**: `0 config file(s)`と表示される

**解決方法**:
```bash
# 設定ファイルを追加
echo "hostname router1" > D:\networks\example\router1.cfg
echo "hostname switch1" > D:\networks\example\switch1.cfg
```

### 問題2: ファイル名に不正な文字

**症状**: 422エラーまたはファイル名のエラー

**解決方法**:
- ファイル名から特殊文字を削除
- スペースをハイフンまたはアンダースコアに置換
- 日本語のファイル名を英数字に変更

**Before**: `ルーター 1.cfg`
**After**: `router-1.cfg`

### 問題3: フォルダが深すぎる

**症状**: 一部のファイルが認識されない

**解決方法**:
- フラットなディレクトリ構造を使用
- または、すべてのファイルを1つのフォルダに集約

### 問題4: ファイルサイズ制限超過

**症状**: 422エラーまたは413エラー

**制限**:
- 個別ファイル: 最大10MB
- 合計アップロード: 最大100MB

**解決方法**:
- 大きなファイルを分割
- 不要な設定を削除

## 詳細なデバッグログの取得

### バックエンドの詳細ログ

```bash
# WSL Ubuntuターミナルで
cd ~/batfish_vis/backend
source .venv/bin/activate

# ログレベルをDEBUGに設定
export LOG_LEVEL=DEBUG

# uvicornの詳細ログを有効化
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### フロントエンドのデバッグログ

SnapshotUpload.jsにログを追加:

```javascript
// handleFileSelection関数内
console.log('Files selected:', selectedFiles);
console.log('File count:', selectedFiles.length);
selectedFiles.forEach((file, idx) => {
  console.log(`File ${idx + 1}:`, file.name, file.size, 'bytes');
});
```

### curlでテスト

バックエンドを直接テスト:

```bash
# WSLターミナルで
curl -X POST http://localhost:8000/api/snapshots \
  -F "snapshotName=test-curl" \
  -F "networkName=default" \
  -F "configFiles=@/mnt/d/networks/example/router1.cfg" \
  -F "configFiles=@/mnt/d/networks/example/switch1.cfg"
```

**成功の場合**: フロントエンドに問題がある

**失敗の場合**: バックエンドまたはBatfishに問題がある

## まとめ

**422エラーの主な原因**:
1. ✅ ファイルデータが送信されていない
2. ✅ フォームフィールド名が不一致
3. ✅ 必須パラメータが欠落
4. ✅ Content-Typeが不正

**診断手順**:
1. ブラウザのコンソールでファイル数を確認
2. ネットワークタブでリクエスト内容を確認
3. バックエンドログでエラー詳細を確認
4. 最小限のテストケースで動作確認

**解決策**:
1. 個別ファイル選択モードでテスト
2. ブラウザキャッシュをクリア
3. 最新のコードを使用
4. curlで直接テスト

詳細なログを確認することで、422エラーの正確な原因を特定できます。
