# 422エラー デバッグのための変更内容

## 変更日時
2025-11-22

## 変更の目的

`D:\networks\example` フォルダをアップロードすると422 Unprocessable Entityエラーが発生する問題について、詳細なデバッグログを追加しました。

## 変更されたファイル

### 1. `frontend/src/components/SnapshotUpload.js`

#### 変更箇所1: handleFileSelection関数にデバッグログを追加

**行166-176付近**

```javascript
// Handle file selection
function handleFileSelection(event) {
  console.log('[DEBUG] handleFileSelection called');
  console.log('[DEBUG] event.target.id:', event.target.id);
  console.log('[DEBUG] event.target.files:', event.target.files);
  console.log('[DEBUG] event.target.files.length:', event.target.files ? event.target.files.length : 'null');

  selectedFiles = Array.from(event.target.files);
  console.log('[DEBUG] selectedFiles after Array.from:', selectedFiles);
  console.log('[DEBUG] selectedFiles.length:', selectedFiles.length);

  const fileCount = container.querySelector('#file-count');
  // ... 以下省略
```

**目的**:
- ファイル選択時に何が起きているかを追跡
- `event.target.files` が空かどうかを確認
- `Array.from()` が正しく動作しているかを確認

#### 変更箇所2: handleSubmit関数にデバッグログを追加

**行231-236、245-251付近**

```javascript
// Debug: Log submission details
console.log('[DEBUG] Form submission starting');
console.log('[DEBUG] snapshotName:', snapshotName);
console.log('[DEBUG] networkName:', networkName);
console.log('[DEBUG] selectedFiles count:', selectedFiles.length);
console.log('[DEBUG] selectedFiles:', selectedFiles);

// Start upload
isUploading = true;
showProgress(true);
hideErrors();
showStatus('Creating snapshot...', 'info');

try {
  console.log('[DEBUG] Calling snapshotService.createSnapshot...');
  const snapshot = await snapshotService.createSnapshot(
    snapshotName,
    networkName,
    selectedFiles
  );
  console.log('[DEBUG] snapshotService.createSnapshot returned:', snapshot);
```

**目的**:
- フォーム送信時のパラメータを確認
- `selectedFiles` が正しく渡されているかを確認
- API呼び出しの前後をトレース

### 2. `frontend/src/services/snapshotService.js`

#### すでに追加済みのデバッグログ（前回の変更）

**行28-34、47-66付近**

```javascript
console.log('[DEBUG] createSnapshot called with:', {
  snapshotName,
  networkName,
  configFiles: configFiles,
  fileCount: configFiles ? configFiles.length : 0,
  fileType: configFiles ? typeof configFiles : 'undefined'
});

if (!configFiles || configFiles.length === 0) {
  console.error('[ERROR] No config files provided');
  throw new Error('At least one configuration file is required');
}

// Create FormData for multipart upload
const formData = new FormData();
formData.append('snapshotName', snapshotName);
formData.append('networkName', networkName);

// Add all configuration files
for (let i = 0; i < configFiles.length; i++) {
  const file = configFiles[i];
  console.log(`[DEBUG] Adding file ${i + 1}:`, {
    name: file.name,
    size: file.size,
    type: file.type,
    lastModified: file.lastModified
  });
  formData.append('configFiles', file);
}

// Log FormData contents
console.log('[DEBUG] FormData entries:');
for (let pair of formData.entries()) {
  if (pair[1] instanceof File) {
    console.log(`  ${pair[0]}: File(${pair[1].name}, ${pair[1].size} bytes)`);
  } else {
    console.log(`  ${pair[0]}: ${pair[1]}`);
  }
}
```

**目的**:
- API呼び出し時のパラメータを確認
- FormDataに正しくファイルが追加されているかを確認
- 各ファイルのメタデータ（名前、サイズ、タイプ）を確認

### 3. `backend/src/api/snapshot_api.py`

#### すでに追加済みのデバッグログ（前回の変更）

**行84-107**

```python
@router.post("", response_model=Snapshot, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    snapshotName: str = Form(...),
    networkName: str = Form(default="default"),
    configFiles: List[UploadFile] = File(...)
):
    # Debug logging for 422 investigation
    logger.info(
        "Snapshot creation request received",
        extra={
            "snapshot": snapshotName,
            "network": networkName,
            "file_count": len(configFiles) if configFiles else 0,
            "files": [f.filename for f in configFiles] if configFiles else []
        }
    )

    # Additional debug: check each file
    if configFiles:
        for idx, file in enumerate(configFiles):
            logger.debug(
                f"File {idx + 1}",
                extra={
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": file.size if hasattr(file, 'size') else "unknown"
                }
            )
    else:
        logger.warning("No config files received in request")
```

**目的**:
- バックエンドが受信したリクエスト内容を確認
- FastAPIのバリデーション前にログ出力（422の場合はここまで到達しない）
- ファイルが正しく受信されているかを確認

## 期待されるログの流れ

### 正常なケース

#### 1. ファイル選択時（ブラウザコンソール）

```
[DEBUG] handleFileSelection called
[DEBUG] event.target.id: config-folder
[DEBUG] event.target.files: FileList { 0: File, 1: File, length: 2 }
[DEBUG] event.target.files.length: 2
[DEBUG] selectedFiles after Array.from: Array(2) [ File, File ]
[DEBUG] selectedFiles.length: 2
```

#### 2. フォーム送信時（ブラウザコンソール）

```
[DEBUG] Form submission starting
[DEBUG] snapshotName: test-debug
[DEBUG] networkName: default
[DEBUG] selectedFiles count: 2
[DEBUG] selectedFiles: Array(2) [ File { name: "router1.cfg", size: 123, ... }, File { name: "switch1.cfg", size: 98, ... } ]
[DEBUG] Calling snapshotService.createSnapshot...
```

#### 3. API呼び出し時（ブラウザコンソール）

```
[DEBUG] createSnapshot called with: {
  snapshotName: "test-debug",
  networkName: "default",
  configFiles: Array(2),
  fileCount: 2,
  fileType: "object"
}
[DEBUG] Adding file 1: { name: "router1.cfg", size: 123, type: "text/plain", lastModified: 1732273200000 }
[DEBUG] Adding file 2: { name: "switch1.cfg", size: 98, type: "text/plain", lastModified: 1732273201000 }
[DEBUG] FormData entries:
  snapshotName: test-debug
  networkName: default
  configFiles: File(router1.cfg, 123 bytes)
  configFiles: File(switch1.cfg, 98 bytes)
Creating snapshot: test-debug with 2 files
```

#### 4. バックエンド受信時（WSL Ubuntuターミナル）

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
DEBUG: File 2
  filename: switch1.cfg
  content_type: text/plain
  size: 98
```

### 異常なケース（422エラー）

#### ケース1: ファイルが選択されていない

```
[DEBUG] handleFileSelection called
[DEBUG] event.target.id: config-folder
[DEBUG] event.target.files: FileList { length: 0 }
[DEBUG] event.target.files.length: 0
[DEBUG] selectedFiles after Array.from: Array(0)
[DEBUG] selectedFiles.length: 0
```

→ フォーム送信時に「Please select at least one configuration file」エラーが表示される

#### ケース2: FormDataにファイルが追加されない

```
[DEBUG] Form submission starting
[DEBUG] selectedFiles count: 2
[DEBUG] createSnapshot called with: { fileCount: 2 }
[DEBUG] Adding file 1: { name: "router1.cfg", size: 0, type: "", lastModified: 0 }
[DEBUG] Adding file 2: { name: "switch1.cfg", size: 0, type: "", lastModified: 0 }
[DEBUG] FormData entries:
  snapshotName: test-debug
  networkName: default
  configFiles: File(router1.cfg, 0 bytes)
  configFiles: File(switch1.cfg, 0 bytes)
```

→ サイズが0のファイルはバックエンドで拒否される可能性がある

#### ケース3: バックエンドに到達しない（422エラー）

```
(ブラウザコンソール)
[DEBUG] FormData entries:
  snapshotName: test-debug
  networkName: default
  (configFilesが含まれていない)

(バックエンドログ)
(ログが全く表示されない)
```

→ FastAPIがバリデーションエラーでリクエストを拒否している

## デバッグ手順

### 手順1: ブラウザキャッシュをクリア

変更が反映されていることを確認するため。

### 手順2: ブラウザコンソールを開く

F12 → Console タブ

### 手順3: フォルダをアップロード

1. Select Folder を選択
2. D:\networks\example を選択
3. Snapshot Name: test-debug
4. Create Snapshot をクリック

### 手順4: ログを確認

上記「期待されるログの流れ」と比較して、どこで問題が発生しているかを特定。

### 手順5: 結果を報告

以下の情報をコピーして報告：

1. **ブラウザコンソールログ**: `[DEBUG]` で始まる行をすべてコピー
2. **フォルダ内容**: `dir D:\networks\example` の出力
3. **バックエンドログ**: WSL Ubuntuターミナルの出力
4. **Networkタブ**: POST /api/snapshotsのPayload

## 作成されたドキュメント

1. **`docs/422_error_debug_changes.md`** (このファイル) - 変更内容の詳細
2. **`docs/frontend_debug_steps.md`** - 詳細なデバッグ手順
3. **`docs/422_error_quick_steps.md`** - クイックリファレンス

## 次のステップ

ユーザーは以下を実施してください：

1. ブラウザキャッシュをクリア（Ctrl+Shift+Delete）
2. フロントエンドを再起動（npm run dev）
3. ブラウザコンソールを開く（F12 → Console）
4. フォルダをアップロード
5. コンソールログをすべてコピーして報告

これにより、問題の正確な原因を特定できます。
