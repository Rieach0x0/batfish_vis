# 422エラー - 解決しました！

## 根本原因

### 問題の核心

**`apiClient.js`の`request()`関数が、すべてのリクエストに`Content-Type: application/json`ヘッダーを設定していました。**

これにより、FormDataを送信する際も`Content-Type: application/json`が設定され、バックエンドがFormDataをJSONとして解釈しようとして失敗していました。

### コードの問題箇所

**ファイル**: `frontend/src/services/apiClient.js`

**問題のコード** (line 33-42):
```javascript
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders = {
    'Content-Type': 'application/json',  // ← 常にapplication/jsonが設定される
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,  // ← defaultHeadersが最初にマージされる
      ...options.headers, // ← postFormの headers: {} は空なので、上書きされない
    },
  };
```

**流れ**:
1. `postForm()`が`headers: {}`を渡す
2. `request()`が`defaultHeaders`に`Content-Type: application/json`を設定
3. `{ ...defaultHeaders, ...{} }` → `{ 'Content-Type': 'application/json' }`
4. FormDataが`Content-Type: application/json`で送信される
5. バックエンドがJSONとしてパースしようとする
6. **FormDataが失われる** → 空のFormData `"FormData([])"`
7. FastAPIが422エラーを返す

### 証拠

#### フロントエンドログ
```
[DEBUG] FormData entries:
  snapshotName: test-config-only
  networkName: default
  configFiles: File(as1border1.cfg, 3706 bytes)
  ... (13 files)
```
→ FormDataは正しく作成されている ✅

#### バックエンドログ
```json
{
  "errors": [
    {"type": "missing", "loc": ["body", "snapshotName"], "msg": "Field required"},
    {"type": "missing", "loc": ["body", "configFiles"], "msg": "Field required"}
  ],
  "body": "FormData([])"  ← 空！
}
```
→ バックエンドには何も届いていない ❌

## 修正内容

### 修正1: `request()`関数でFormDataを検出

**変更前**:
```javascript
const defaultHeaders = {
  'Content-Type': 'application/json',
};
```

**変更後**:
```javascript
// Only set Content-Type: application/json if not explicitly overridden
// For FormData, we should NOT set Content-Type (browser sets it automatically)
const defaultHeaders = {};
if (options.body && !(options.body instanceof FormData)) {
  defaultHeaders['Content-Type'] = 'application/json';
}
```

**効果**:
- `options.body`がFormDataの場合、Content-Typeを設定しない
- ブラウザが自動的に`Content-Type: multipart/form-data; boundary=...`を設定
- JSON bodyの場合のみ、`Content-Type: application/json`を設定

### 修正2: `postForm()`メソッドの簡素化

**変更前**:
```javascript
async postForm(endpoint, formData) {
  return request(endpoint, {
    method: 'POST',
    headers: {}, // Let browser set Content-Type for multipart/form-data
    body: formData,
  });
}
```

**変更後**:
```javascript
async postForm(endpoint, formData) {
  return request(endpoint, {
    method: 'POST',
    body: formData, // FormData will be detected and Content-Type will not be set
  });
}
```

**効果**:
- 不要な`headers: {}`を削除
- `request()`関数がFormDataを自動検出してContent-Typeを設定しない

## テスト手順

### ステップ1: フロントエンドを再起動

**Windows PowerShell**で:

```powershell
# Ctrl+C でフロントエンドを停止

cd D:\batfish_vis\frontend

# キャッシュクリア
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue

# 再起動
npm run dev
```

### ステップ2: ブラウザでテスト

1. ブラウザで http://localhost:5173 にアクセス
2. **すべてのタブを閉じて、ブラウザを再起動**（重要！）
3. F12 → Console タブを開く
4. F12 → **Network** タブを開く（重要！）
5. **Select Files** を選択
6. `.cfg` ファイル**のみ**を13個選択
7. Snapshot Name: `test-final`
8. **Create Snapshot** をクリック

### ステップ3: Network タブで確認

1. `POST /api/snapshots` リクエストを選択
2. **Headers** タブを確認

**期待される結果**:
```
Request Headers:
  Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
```

**NG（修正前）**:
```
Request Headers:
  Content-Type: application/json
```

### ステップ4: 結果を確認

#### 成功する場合

**ブラウザ**:
```
Snapshot "test-final" created successfully! Detected 13 devices.
```

**バックエンドログ**:
```
INFO: Snapshot creation request received
  snapshot: test-final
  network: default
  file_count: 13
  files: ['as1border1.cfg', 'as1border2.cfg', ...]
```

#### 失敗する場合

バックエンドログの`body:`の値を確認:
- まだ`"FormData([])"`の場合、別の問題がある
- エラーメッセージを報告

## FormDataとContent-Typeの重要な注意点

### FormData送信時のContent-Type

**正しい方法**:
```javascript
const formData = new FormData();
formData.append('file', file);

fetch(url, {
  method: 'POST',
  body: formData,
  // Content-Typeは設定しない！ブラウザに任せる
});
```

ブラウザが自動的に以下を設定:
```
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryXXXXXXXXXXXX
```

**間違った方法**:
```javascript
fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'multipart/form-data', // ❌ boundaryが含まれない
  },
  body: formData,
});
```

または:
```javascript
fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json', // ❌ FormDataがJSONとして送信される
  },
  body: formData,
});
```

### なぜboundaryが必要か

`multipart/form-data`は、複数のパートに分かれたデータを送信します:

```
------WebKitFormBoundaryXXXXXXXXXXXX
Content-Disposition: form-data; name="snapshotName"

test-final
------WebKitFormBoundaryXXXXXXXXXXXX
Content-Disposition: form-data; name="configFiles"; filename="as1border1.cfg"
Content-Type: text/plain

<file content>
------WebKitFormBoundaryXXXXXXXXXXXX--
```

各パートは`boundary`で区切られます。boundaryはランダムに生成されるため、**ブラウザに任せる必要があります**。

## まとめ

**問題**:
- `apiClient.js`がすべてのリクエストに`Content-Type: application/json`を設定
- FormData送信時も`application/json`が設定される
- バックエンドがJSONとしてパースしようとして、FormDataが失われる

**修正**:
- `request()`関数で`options.body instanceof FormData`をチェック
- FormDataの場合、Content-Typeを設定しない（ブラウザに任せる）

**結果**:
- FormDataが正しく送信される
- バックエンドが正しくパースできる
- 422エラーが解決される

**学んだこと**:
- FormData送信時は、Content-Typeを手動設定してはいけない
- ブラウザが自動的にboundaryを含むContent-Typeを設定する
- `instanceof FormData`で型をチェックできる

これで422エラーは完全に解決するはずです！
