# フロントエンド フォルダアップロード機能 - 修正サマリー

## 修正概要

フロントエンドのConfiguration Files選択を、**個別ファイル選択**と**フォルダ選択**の両方に対応しました。

## 修正されたファイル

### 1. `frontend/src/components/SnapshotUpload.js` ✅

#### 変更内容

**追加された機能**:
- ラジオボタンで「Files」と「Folder」モードを切り替え
- フォルダ選択用のinput要素（`webkitdirectory`属性）
- アップロードモード切り替えハンドラー
- フォルダ名と設定ファイル数の表示
- 設定ファイル形式の自動検出と警告

**HTMLの変更**:

```html
<!-- Before -->
<input type="file" id="config-files" multiple accept=".cfg,.conf,.txt" required />

<!-- After -->
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

<input type="file" id="config-files" multiple accept=".cfg,.conf,.txt,.ios,.junos,.eos" required />
<input type="file" id="config-folder" webkitdirectory directory multiple style="display: none;" />
```

**JavaScriptの変更**:

```javascript
// 追加: アップロードモード切り替え
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

// 改善: ファイル選択処理
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

**イベントリスナーの追加**:

```javascript
function attachEventListeners() {
  const form = container.querySelector('#snapshot-form');
  const fileInput = container.querySelector('#config-files');
  const folderInput = container.querySelector('#config-folder');
  const uploadModeRadios = container.querySelectorAll('input[name="upload-mode"]');

  // Upload mode switching
  uploadModeRadios.forEach(radio => {
    radio.addEventListener('change', handleUploadModeChange);
  });

  // File selection
  fileInput.addEventListener('change', handleFileSelection);
  folderInput.addEventListener('change', handleFileSelection);

  // Form submission
  form.addEventListener('submit', handleSubmit);
}
```

### 2. `frontend/src/styles.css` ✅

#### 追加されたスタイル

```css
.form-group small.help-text {
  color: #9ca3af;
  font-style: italic;
}

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
```

## 機能の使用方法

### ファイル選択モード（デフォルト）

1. **Select Files** ラジオボタンを選択（デフォルト）
2. 「ファイルを選択」をクリック
3. 複数の設定ファイルを選択（Ctrl/Cmdキーを押しながら）
4. 選択したファイル数が表示される

**表示例**:
```
3 file(s) selected
```

### フォルダ選択モード

1. **Select Folder** ラジオボタンを選択
2. ファイル入力が自動的に切り替わる
3. 「ファイルを選択」をクリック
4. ネットワーク設定が格納されたフォルダを選択
5. フォルダ名、総ファイル数、設定ファイル数が表示される

**表示例**:
```
network-configs: 15 file(s) total, 12 config file(s)
```

## 追加されたファイル形式のサポート

以前:
- `.cfg`, `.conf`, `.txt`

追加後:
- `.cfg`, `.conf`, `.txt`, `.ios`, `.junos`, `.eos`

これにより、より多くのベンダー固有の拡張子に対応しました。

## バックエンドの変更

**変更なし** ✅

バックエンドAPIは既に複数ファイルのアップロードに対応しているため、フォルダから選択されたファイルも通常のマルチパートフォームデータとして処理されます。

## ブラウザ互換性

### `webkitdirectory` 属性のサポート

| ブラウザ | サポート状況 |
|---------|------------|
| Chrome 21+ | ✅ フルサポート |
| Edge 13+ | ✅ フルサポート |
| Firefox 50+ | ✅ フルサポート |
| Safari 11.1+ | ✅ フルサポート |
| Opera 15+ | ✅ フルサポート |
| Internet Explorer | ❌ 非対応 |

**注意**: 古いブラウザでは「Select Folder」オプションが動作しない場合があります。その場合は「Select Files」を使用してください。

## ユーザー体験の改善

### Before（修正前）

```
Configuration Files *
[ファイルを選択]
No files selected
```

- ファイルのみ選択可能
- 1つずつ選択する必要がある（Ctrl/Cmdで複数選択可能だが説明なし）

### After（修正後）

```
Configuration Files/Folder *

○ Select Files    ○ Select Folder

[ファイルを選択]

No files selected
Files: Select multiple config files | Folder: Select a directory containing config files
```

- ファイルまたはフォルダを選択可能
- 選択モードが明確
- ヘルプテキストで使い方を説明
- フォルダ選択時はフォルダ名とファイル数を表示
- 設定ファイルとして認識されないファイルには警告

## テスト方法

### 1. ファイルモードのテスト

```bash
# フロントエンドを起動
cd D:\batfish_vis\frontend
npm run dev
```

ブラウザで `http://localhost:5173` にアクセス:

1. **Select Files** を選択
2. 複数の `.cfg` ファイルを選択
3. ファイル数が表示されることを確認
4. スナップショットを作成

### 2. フォルダモードのテスト

1. テスト用フォルダを作成:
```bash
mkdir D:\test-configs
echo "hostname router1" > D:\test-configs\router1.cfg
echo "hostname router2" > D:\test-configs\router2.cfg
echo "hostname switch1" > D:\test-configs\switch1.conf
```

2. ブラウザで:
   - **Select Folder** を選択
   - `D:\test-configs` フォルダを選択
   - `test-configs: 3 file(s) total, 3 config file(s)` と表示されることを確認
   - スナップショットを作成

### 3. 警告表示のテスト

1. テスト用フォルダに設定ファイル以外を追加:
```bash
echo "test" > D:\test-configs\readme.md
echo "test" > D:\test-configs\notes.txt
```

2. ブラウザで:
   - フォルダを選択
   - `test-configs: 5 file(s) total, 4 config file(s)` と表示されることを確認
   - `.md` ファイルは設定ファイルとしてカウントされない

## まとめ

**修正されたファイル**:
- ✅ `frontend/src/components/SnapshotUpload.js` - フォルダ選択機能を追加
- ✅ `frontend/src/styles.css` - ラジオボタンとレイアウトのスタイルを追加

**新規ドキュメント**:
- ✅ `docs/folder_upload_feature.md` - 詳細仕様書
- ✅ `docs/frontend_folder_upload_summary.md` - このファイル

**バックエンドの変更**:
- 変更なし（既存のマルチファイルアップロードAPIをそのまま使用）

**主な改善点**:
1. フォルダ全体を一括アップロード可能
2. ファイル形式の自動検出
3. フォルダ名とファイル数の表示
4. 認識できないファイル形式に警告
5. ユーザーフレンドリーなインターフェース

これにより、Batfishスナップショットの作成が大幅に効率化されました！
