# フロントエンド デバッグ手順 - 422エラー調査

## 現状

`D:\networks\example` フォルダをアップロードすると、422 Unprocessable Entity エラーが発生します。
デバッグログを追加しましたが、「出力内容は変化しない」という状況です。

## なぜログが表示されないか？

以下の可能性があります：

1. **ブラウザキャッシュ**: 古いJavaScriptファイルがキャッシュされている
2. **フロントエンド未再起動**: Vite dev serverが更新を検知していない
3. **WSL同期問題**: WindowsとWSL間でファイルが同期されていない（該当する場合）
4. **ブラウザコンソールを開いていない**: console.logはコンソールを開かないと見えない

## 手順1: ブラウザキャッシュをクリア

### Chrome の場合

1. **F12** キーを押してデベロッパーツールを開く
2. デベロッパーツールが開いた状態で、ページの **更新ボタン** を **右クリック**
3. **「キャッシュの消去とハード再読み込み」** を選択

または：

1. **Ctrl + Shift + Delete** を押す
2. 「キャッシュされた画像とファイル」にチェック
3. 「データを削除」をクリック

### Edge の場合

同じく **Ctrl + Shift + Delete** でキャッシュクリア

## 手順2: フロントエンドの完全再起動

### Windows PowerShellで

```powershell
# 現在のフロントエンドを停止（Ctrl+C）

# ディレクトリに移動
cd D:\batfish_vis\frontend

# node_modulesとdistをクリーン（オプション）
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# 再起動
npm run dev
```

## 手順3: ブラウザコンソールでログを確認

1. ブラウザで **http://localhost:5173** にアクセス
2. **F12** キーを押してデベロッパーツールを開く
3. **Console** タブを選択
4. コンソールをクリアするため、左上の **🚫 Clear console** ボタンをクリック

## 手順4: フォルダアップロードをテスト

### 4-1: フォルダ内容を確認

まず、`D:\networks\example` フォルダに実際にファイルがあるか確認：

```powershell
# Windows PowerShellで
dir D:\networks\example
```

**もしフォルダが空なら、テストファイルを作成**:

```powershell
# フォルダを作成（存在しない場合）
mkdir D:\networks\example -ErrorAction SilentlyContinue

# テスト用設定ファイルを作成
@"
hostname router1
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
"@ | Out-File -FilePath "D:\networks\example\router1.cfg" -Encoding ascii

@"
hostname switch1
interface FastEthernet0/1
 switchport mode access
"@ | Out-File -FilePath "D:\networks\example\switch1.cfg" -Encoding ascii

# 確認
dir D:\networks\example
```

### 4-2: フォルダをアップロード

1. ブラウザで **Select Folder** ラジオボタンを選択
2. **「ファイルを選択」** をクリック
3. `D:\networks\example` フォルダを選択
4. **Snapshot Name** に `test-debug` と入力
5. **Create Snapshot** をクリック

### 4-3: コンソールログを確認

ブラウザのConsoleタブに以下のようなログが表示されるはずです：

```javascript
[DEBUG] handleFileSelection called
[DEBUG] event.target.id: config-folder
[DEBUG] event.target.files: FileList { 0: File, 1: File, length: 2 }
[DEBUG] event.target.files.length: 2
[DEBUG] selectedFiles after Array.from: Array(2) [ File, File ]
[DEBUG] selectedFiles.length: 2
```

**Create Snapshotをクリック後**:

```javascript
[DEBUG] Form submission starting
[DEBUG] snapshotName: test-debug
[DEBUG] networkName: default
[DEBUG] selectedFiles count: 2
[DEBUG] selectedFiles: Array(2) [ File, File ]
[DEBUG] Calling snapshotService.createSnapshot...
[DEBUG] createSnapshot called with: { snapshotName: "test-debug", networkName: "default", configFiles: Array(2), fileCount: 2 }
[DEBUG] Adding file 1: { name: "router1.cfg", size: 123, type: "text/plain" }
[DEBUG] Adding file 2: { name: "switch1.cfg", size: 98, type: "text/plain" }
[DEBUG] FormData entries:
  snapshotName: test-debug
  networkName: default
  configFiles: File(router1.cfg, 123 bytes)
  configFiles: File(switch1.cfg, 98 bytes)
Creating snapshot: test-debug with 2 files
```

## 手順5: ログの結果を解析

### ケース1: ログが全く表示されない

**原因**: キャッシュまたはフロントエンド未更新

**対策**:
1. 手順1と手順2を再実行
2. ブラウザを完全に閉じて再起動
3. シークレットモード / プライベートブラウジングで試す

### ケース2: `selectedFiles.length: 0` と表示される

**原因**: フォルダ選択ダイアログでフォルダが正しく選択されていない、またはフォルダが空

**対策**:
1. `D:\networks\example` フォルダにファイルが存在するか確認（手順4-1）
2. 「Select Files」モードで個別ファイルを選択してテスト
3. 別のフォルダで試す

### ケース3: `fileCount: 0` と表示される（snapshotService内）

**原因**: `selectedFiles` 配列が空のFileオブジェクトを含んでいる

**対策**:
- 各ファイルの `size` を確認（ログに表示される）
- サイズが0のファイルは無効

### ケース4: FormDataは正しいが422エラー

**原因**: バックエンドのバリデーションエラー

**対策**:
- バックエンドログを確認（WSL Ubuntuターミナル）
- `logs/422_error_troubleshooting.md` を参照

## 手順6: 個別ファイル選択でテスト

フォルダモードで問題がある場合、個別ファイル選択でテスト：

1. **Select Files** ラジオボタンを選択
2. **「ファイルを選択」** をクリック
3. `D:\networks\example` フォルダを開く
4. **Ctrl + A** ですべてのファイルを選択
5. **「開く」** をクリック
6. **Create Snapshot** をクリック

**これで成功する場合**: フォルダモード固有の問題
**これでも失敗する場合**: バックエンドまたはファイル自体の問題

## 手順7: Network タブでリクエストを確認

1. デベロッパーツールで **Network** タブを開く
2. フォルダをアップロード
3. `POST /api/snapshots` リクエストを選択
4. **Headers** タブで `Content-Type: multipart/form-data` を確認
5. **Payload** タブでファイルが含まれているか確認

**正常なPayload**:
```
------WebKitFormBoundary...
Content-Disposition: form-data; name="snapshotName"

test-debug
------WebKitFormBoundary...
Content-Disposition: form-data; name="networkName"

default
------WebKitFormBoundary...
Content-Disposition: form-data; name="configFiles"; filename="router1.cfg"
Content-Type: text/plain

<file content>
------WebKitFormBoundary...
```

**異常なPayload（422の原因）**:
```
------WebKitFormBoundary...
Content-Disposition: form-data; name="snapshotName"

test-debug
------WebKitFormBoundary...
Content-Disposition: form-data; name="networkName"

default
------WebKitFormBoundary...
(ファイルが含まれていない)
```

## 手順8: バックエンドログを確認

WSL Ubuntuターミナルで：

```bash
# バックエンドのログを確認
cd ~/batfish_vis/backend

# ログレベルをDEBUGに設定（.envファイル）
cat .env

# 出力例:
# BATFISH_HOST=localhost
# BATFISH_PORT=9996
# LOG_LEVEL=DEBUG

# バックエンドを再起動
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

**正常なログ**:
```
INFO: Snapshot creation request received
  snapshot: test-debug
  network: default
  file_count: 2
  files: ['router1.cfg', 'switch1.cfg']
DEBUG: File 1
  filename: router1.cfg
  content_type: text/plain
  size: 123
```

**異常なログ（422の原因）**:
```
(ログが全く表示されない - FastAPIがバリデーションエラーでリクエストを拒否)
```

## 手順9: 最小限のテスト

最も単純なテストケース：

```powershell
# 1つの小さなファイルを作成
"hostname test" | Out-File -FilePath "D:\networks\example\minimal.cfg" -Encoding ascii

# ファイルサイズを確認
(Get-Item "D:\networks\example\minimal.cfg").Length
# 出力: 15 (bytes)
```

ブラウザで：
1. **Select Files** を選択
2. `minimal.cfg` のみを選択
3. Snapshot Name: `test-minimal`
4. **Create Snapshot** をクリック

## 次のステップ

このドキュメントの手順を実行した後、以下の情報を提供してください：

### 提供してほしい情報

1. **ブラウザコンソールログ**:
   - `[DEBUG]` で始まる行をすべてコピー
   - エラーがあれば、エラーメッセージも

2. **フォルダ内容**:
   ```powershell
   dir D:\networks\example
   ```
   の出力

3. **Network タブ**:
   - `POST /api/snapshots` のStatusコード
   - Payloadタブの内容（スクリーンショットでも可）

4. **バックエンドログ**:
   - WSL Ubuntuターミナルに表示されたログ

5. **どの手順で成功/失敗したか**:
   - 個別ファイル選択: 成功/失敗
   - フォルダ選択: 成功/失敗
   - 最小限のテスト: 成功/失敗

これらの情報があれば、問題の正確な原因を特定できます。

## よくある原因まとめ

| 症状 | 原因 | 解決方法 |
|------|------|----------|
| ログが表示されない | ブラウザキャッシュ | Ctrl+Shift+Delete でクリア |
| `fileCount: 0` | フォルダが空 | テストファイルを作成 |
| `selectedFiles.length: 0` | フォルダ選択失敗 | 個別ファイル選択でテスト |
| 422エラー（Payloadにファイルなし） | FormData作成失敗 | Console ログで確認 |
| 422エラー（Payloadにファイルあり） | バックエンドバリデーション | バックエンドログ確認 |

## 緊急対応: curlでバックエンドを直接テスト

フロントエンドをバイパスしてバックエンドをテスト：

```bash
# WSL Ubuntuターミナルで
curl -X POST http://localhost:8000/api/snapshots \
  -F "snapshotName=test-curl" \
  -F "networkName=default" \
  -F "configFiles=@/mnt/d/networks/example/router1.cfg" \
  -F "configFiles=@/mnt/d/networks/example/switch1.cfg"
```

**これで成功する場合**: フロントエンドに問題
**これでも失敗する場合**: バックエンドまたはBatfishに問題
