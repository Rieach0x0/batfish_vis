# 422エラー - クイックデバッグ手順

## 最初に確認すること

### 1. フォルダにファイルがあるか確認

```powershell
dir D:\networks\example
```

**フォルダが空または存在しない場合**:

```powershell
# フォルダ作成
mkdir D:\networks\example

# テストファイル作成
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
```

### 2. ブラウザキャッシュをクリア

1. **F12** を押してデベロッパーツールを開く
2. 更新ボタンを **右クリック**
3. **「キャッシュの消去とハード再読み込み」** を選択

### 3. フロントエンドを再起動

```powershell
# Ctrl+C でフロントエンドを停止

cd D:\batfish_vis\frontend
npm run dev
```

### 4. ブラウザコンソールを開く

1. **F12** → **Console** タブ
2. コンソールをクリア（🚫 Clear consoleボタン）

### 5. フォルダをアップロード

1. **Select Folder** を選択
2. `D:\networks\example` を選択
3. Snapshot Name: `test-debug`
4. **Create Snapshot** をクリック

### 6. コンソールログを確認

**期待されるログ**:
```
[DEBUG] handleFileSelection called
[DEBUG] selectedFiles.length: 2
[DEBUG] Form submission starting
[DEBUG] selectedFiles count: 2
[DEBUG] createSnapshot called with: { fileCount: 2 }
[DEBUG] Adding file 1: { name: "router1.cfg", size: 123 }
[DEBUG] Adding file 2: { name: "switch1.cfg", size: 98 }
```

## ログが表示されない場合

1. ブラウザを完全に閉じて再起動
2. シークレットモードで試す
3. 別のブラウザ（Edge/Firefoxなど）で試す

## `fileCount: 0` と表示される場合

**原因**: フォルダが正しく選択されていない、またはフォルダが空

**解決方法**:
1. フォルダ内容を再確認（上記手順1）
2. 「Select Files」モードで個別にファイルを選択してテスト
   - **Select Files** を選択
   - `D:\networks\example` を開く
   - **Ctrl+A** ですべてのファイルを選択
   - **開く** をクリック

## FormDataは正しいが422エラーが出る場合

**バックエンドログを確認**:

WSL Ubuntuターミナルで：

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

再度アップロードして、ログを確認。

**期待されるログ**:
```
INFO: Snapshot creation request received
  snapshot: test-debug
  network: default
  file_count: 2
  files: ['router1.cfg', 'switch1.cfg']
```

**ログが表示されない場合**: FastAPIがバリデーションエラーでリクエストを拒否している

## curlで直接テスト

フロントエンドをバイパスしてテスト：

```bash
# WSL Ubuntuで
curl -X POST http://localhost:8000/api/snapshots \
  -F "snapshotName=test-curl" \
  -F "networkName=default" \
  -F "configFiles=@/mnt/d/networks/example/router1.cfg" \
  -F "configFiles=@/mnt/d/networks/example/switch1.cfg"
```

- **成功する**: フロントエンドに問題
- **失敗する**: バックエンドに問題

## 報告してほしい情報

以下の情報をコピーして共有してください：

### 1. フォルダ内容
```powershell
dir D:\networks\example
```

### 2. ブラウザコンソールログ
`[DEBUG]` で始まる行をすべてコピー

### 3. Networkタブ
- **F12** → **Network** タブ
- `POST /api/snapshots` を選択
- **Payload** タブの内容

### 4. バックエンドログ
WSL Ubuntuターミナルに表示されたログ

### 5. テスト結果
- [ ] 個別ファイル選択: 成功/失敗
- [ ] フォルダ選択: 成功/失敗
- [ ] curl テスト: 成功/失敗

## 詳細なトラブルシューティング

より詳しい手順は `docs/frontend_debug_steps.md` を参照してください。
