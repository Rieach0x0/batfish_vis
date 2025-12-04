# フォルダアップロード機能

## 概要

Batfishは、ネットワーク機器のコンフィグファイルが格納されたフォルダを一括でアップロードできます。この機能により、複数のデバイス設定を効率的に管理できます。

## Batfishの仕様

### ディレクトリ構造

Batfishは以下のようなディレクトリ構造を想定しています：

```
network-configs/
├── router1.cfg
├── router2.cfg
├── switch1.conf
├── switch2.conf
└── firewall.txt
```

または、サブディレクトリを含む構造も可能：

```
network-configs/
├── routers/
│   ├── router1.cfg
│   └── router2.cfg
├── switches/
│   ├── switch1.conf
│   └── switch2.conf
└── firewalls/
    └── firewall.txt
```

### サポートされるファイル形式

Batfishは以下のベンダーの設定ファイルをサポートしています：

- **Cisco IOS/IOS-XE**: `.cfg`, `.conf`, `.txt`
- **Juniper JunOS**: `.junos`, `.conf`, `.txt`
- **Arista EOS**: `.eos`, `.conf`, `.txt`
- **Palo Alto**: `.conf`, `.txt`
- その他のベンダー

### ファイル命名規則

- ファイル名がホスト名として使用されます（拡張子を除く）
  - 例: `router1.cfg` → ホスト名: `router1`
- 特殊文字やスペースは避けることを推奨
- 英数字、ハイフン、アンダースコアが推奨

## フロントエンドの実装

### ユーザーインターフェース

#### 1. アップロードモード選択

ラジオボタンで2つのモードを選択：

```
○ Select Files    ○ Select Folder
```

- **Select Files**: 複数の個別ファイルを選択
- **Select Folder**: フォルダを選択（フォルダ内のすべてのファイルを含む）

#### 2. ファイル入力

**Files モード**:
```html
<input type="file" multiple accept=".cfg,.conf,.txt,.ios,.junos,.eos" />
```

**Folder モード**:
```html
<input type="file" webkitdirectory directory multiple />
```

#### 3. 選択状態の表示

**Files モード**:
```
3 file(s) selected
```

**Folder モード**:
```
network-configs: 15 file(s) total, 12 config file(s)
```

### HTMLコード

```html
<div class="form-group">
  <label>Configuration Files/Folder *</label>

  <div class="file-input-options">
    <div class="radio-group">
      <label class="radio-label">
        <input type="radio" name="upload-mode" value="files" checked />
        <span>Select Files</span>
      </label>
      <label class="radio-label">
        <input type="radio" name="upload-mode" value="folder" />
        <span>Select Folder</span>
      </label>
    </div>
  </div>

  <input
    type="file"
    id="config-files"
    name="configFiles"
    multiple
    accept=".cfg,.conf,.txt,.ios,.junos,.eos"
    required
  />
  <input
    type="file"
    id="config-folder"
    name="configFolder"
    webkitdirectory
    directory
    multiple
    style="display: none;"
  />

  <small id="file-count">No files selected</small>
  <small class="help-text">
    Files: Select multiple config files |
    Folder: Select a directory containing config files
  </small>
</div>
```

### JavaScriptコード

```javascript
// Upload mode change handler
function handleUploadModeChange(event) {
  const mode = event.target.value;
  const fileInput = container.querySelector('#config-files');
  const folderInput = container.querySelector('#config-folder');

  if (mode === 'folder') {
    fileInput.style.display = 'none';
    folderInput.style.display = 'block';
    fileInput.removeAttribute('required');
    folderInput.setAttribute('required', 'required');
  } else {
    fileInput.style.display = 'block';
    folderInput.style.display = 'none';
    fileInput.setAttribute('required', 'required');
    folderInput.removeAttribute('required');
  }

  selectedFiles = [];
  container.querySelector('#file-count').textContent = 'No files selected';
}

// File selection handler
function handleFileSelection(event) {
  selectedFiles = Array.from(event.target.files);
  const fileCount = container.querySelector('#file-count');

  if (selectedFiles.length === 0) {
    fileCount.textContent = 'No files selected';
    fileCount.style.color = '#666';
  } else {
    // Count valid config files
    const configFiles = selectedFiles.filter(file => {
      const ext = file.name.split('.').pop().toLowerCase();
      return ['cfg', 'conf', 'txt', 'ios', 'junos', 'eos'].includes(ext);
    });

    // Display selection info
    if (event.target.id === 'config-folder') {
      // Folder mode: show folder name and file count
      const folderName = selectedFiles[0]?.webkitRelativePath?.split('/')[0] || 'selected folder';
      fileCount.innerHTML = `
        <strong>${folderName}</strong>: ${selectedFiles.length} file(s) total,
        ${configFiles.length} config file(s)
      `;
    } else {
      // File mode: show file count
      fileCount.textContent = `${selectedFiles.length} file(s) selected`;
    }

    fileCount.style.color = '#2563eb';

    // Warn if no valid config files
    if (configFiles.length === 0) {
      fileCount.textContent += ' (Warning: No recognized config files)';
      fileCount.style.color = '#f59e0b';
    }
  }
}
```

### CSSスタイル

```css
/* File input options */
.file-input-options {
  margin-bottom: 1rem;
}

.radio-group {
  display: flex;
  gap: 1.5rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: normal;
}

.radio-label input[type="radio"] {
  width: auto;
  cursor: pointer;
}

.radio-label span {
  font-weight: 500;
  color: #374151;
}

.radio-label input[type="radio"]:checked + span {
  color: var(--primary-color);
  font-weight: 600;
}

.form-group small.help-text {
  color: #9ca3af;
  font-style: italic;
}
```

## バックエンドの処理

バックエンドAPIは変更不要です。フォルダから選択された複数のファイルも、通常のマルチパートフォームデータとして送信されます。

### リクエスト形式

```http
POST /api/snapshots
Content-Type: multipart/form-data

------WebKitFormBoundary
Content-Disposition: form-data; name="snapshotName"

network-snapshot
------WebKitFormBoundary
Content-Disposition: form-data; name="networkName"

default
------WebKitFormBoundary
Content-Disposition: form-data; name="configFiles"; filename="router1.cfg"
Content-Type: text/plain

<router1 config content>
------WebKitFormBoundary
Content-Disposition: form-data; name="configFiles"; filename="router2.cfg"
Content-Type: text/plain

<router2 config content>
------WebKitFormBoundary--
```

## 使用方法

### ステップ1: アップロードモードを選択

1. フロントエンドで「Select Folder」を選択
2. ファイル入力フィールドが自動的に切り替わる

### ステップ2: フォルダを選択

1. 「ファイルを選択」ボタンをクリック
2. ブラウザのフォルダ選択ダイアログが開く
3. ネットワーク設定が格納されたフォルダを選択
4. 「アップロード」または「開く」をクリック

### ステップ3: 選択内容を確認

```
network-configs: 15 file(s) total, 12 config file(s)
```

- フォルダ名、総ファイル数、設定ファイル数が表示される
- 設定ファイルとして認識されたのは12ファイル（.cfg, .conf, .txtなど）

### ステップ4: スナップショットを作成

1. Snapshot Nameを入力（例: `production-2025-11-22`）
2. Network Nameを確認（デフォルト: `default`）
3. 「Create Snapshot」ボタンをクリック

### ステップ5: 結果を確認

成功メッセージ:
```
Snapshot "production-2025-11-22" created successfully! Detected 12 devices.
```

## ブラウザの互換性

### `webkitdirectory` 属性のサポート

| ブラウザ | バージョン | サポート |
|---------|----------|---------|
| Chrome | 21+ | ✅ フルサポート |
| Edge | 13+ | ✅ フルサポート |
| Firefox | 50+ | ✅ フルサポート |
| Safari | 11.1+ | ✅ フルサポート |
| Opera | 15+ | ✅ フルサポート |

**注意**: Internet Explorerはサポートしていません。

### フォールバック

古いブラウザでは「Select Folder」オプションが機能しない場合があります。その場合は「Select Files」モードを使用してください。

## トラブルシューティング

### 問題1: フォルダ選択ダイアログが開かない

**原因**: ブラウザが`webkitdirectory`属性をサポートしていない

**解決方法**:
- Chrome、Firefox、Edge、Safariの最新バージョンを使用
- または「Select Files」モードで個別にファイルを選択

### 問題2: 選択したファイル数が0

**原因**: フォルダ内に認識可能な設定ファイルがない

**解決方法**:
- ファイル拡張子が `.cfg`, `.conf`, `.txt` などであることを確認
- ファイルが空でないことを確認

### 問題3: 一部のファイルが無視される

**原因**: Batfishがサポートしていないファイル形式

**解決方法**:
- 設定ファイルの形式を確認
- Parse Errorsセクションでエラー詳細を確認

### 問題4: アップロードが失敗する

**原因**:
- ファイルサイズ制限超過（個別10MB、合計100MB）
- ネットワークエラー

**解決方法**:
- ファイルサイズを確認
- 不要なファイルを除外
- ネットワーク接続を確認

## セキュリティ考慮事項

### ファイルサイズ制限

バックエンドで設定されている制限:
- **個別ファイル**: 最大10MB
- **合計アップロード**: 最大100MB

### ファイル名のサニタイズ

バックエンドで以下のチェックが実行されます:
- パストラバーサル攻撃の防止
- 英数字、ハイフン、アンダースコア、ドットのみ許可
- 隠しファイル（`.`で始まる）を拒否

### 検証

- 空のファイルを拒否
- 不正なファイル形式を検出
- 設定パース時のエラーを報告

## まとめ

**利点**:
- ✅ フォルダ全体を一括アップロード
- ✅ サブディレクトリを含むディレクトリ構造をサポート
- ✅ ファイル数と種類の自動検出
- ✅ 認識できない形式のファイルに警告

**制限**:
- フォルダサイズ: 最大100MB
- 個別ファイル: 最大10MB
- ブラウザ: モダンブラウザのみ（IE非対応）

**推奨される使用方法**:
1. 小〜中規模ネットワーク（100デバイス未満）: フォルダアップロード
2. 大規模ネットワーク: 複数のスナップショットに分割
3. テスト: 個別ファイル選択

フォルダアップロード機能により、Batfishの使いやすさが大幅に向上します！
