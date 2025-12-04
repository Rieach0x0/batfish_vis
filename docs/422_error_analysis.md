# 422エラー - 原因分析と修正内容

## エラーログ分析結果

### 判明したこと

`D:\batfish_vis\log\frontend_error.log` の分析により、以下が判明しました：

#### ✅ フロントエンドは正常に動作している

1. **ファイル選択**: 18ファイルが正しく選択されている（line 4-7）
2. **FormData作成**: すべてのファイルがFormDataに追加されている（line 34-54）
3. **パラメータ**: `snapshotName: "ex"`, `networkName: "default"` が正しく設定されている

#### ✅ 送信されているファイル一覧

| ファイル名 | サイズ | タイプ | 備考 |
|-----------|--------|--------|------|
| example-network.png | 99,260 bytes | image/png | ⚠️ **画像ファイル** |
| host1.iptables | 578 bytes | (空) | Batfish hosts設定 |
| host2.iptables | 575 bytes | (空) | Batfish hosts設定 |
| host1.json | 197 bytes | application/json | Batfish hosts設定 |
| host2.json | 198 bytes | application/json | Batfish hosts設定 |
| as1border1.cfg | 3,706 bytes | (空) | ✅ ネットワーク設定 |
| as1border2.cfg | 3,847 bytes | (空) | ✅ ネットワーク設定 |
| as1core1.cfg | 1,712 bytes | (空) | ✅ ネットワーク設定 |
| as2border1.cfg | 3,947 bytes | (空) | ✅ ネットワーク設定 |
| as2border2.cfg | 3,837 bytes | (空) | ✅ ネットワーク設定 |
| as2core1.cfg | 2,240 bytes | (空) | ✅ ネットワーク設定 |
| as2core2.cfg | 2,187 bytes | (空) | ✅ ネットワーク設定 |
| as2dept1.cfg | 2,782 bytes | (空) | ✅ ネットワーク設定 |
| as2dist1.cfg | 2,611 bytes | (空) | ✅ ネットワーク設定 |
| as2dist2.cfg | 2,611 bytes | (空) | ✅ ネットワーク設定 |
| as3border1.cfg | 3,473 bytes | (空) | ✅ ネットワーク設定 |
| as3border2.cfg | 3,302 bytes | (空) | ✅ ネットワーク設定 |
| as3core1.cfg | 1,938 bytes | (空) | ✅ ネットワーク設定 |

#### ❌ 問題の原因候補

1. **画像ファイルが含まれている**: `example-network.png` (99KB) は設定ファイルではない
2. **`.iptables` ファイル**: Batfishの `hosts/` ディレクトリ用のファイルだが、ルートディレクトリに配置されている可能性
3. **`.json` ファイル**: 同様にBatfish hosts設定だが、適切な位置にない可能性
4. **FastAPIのバリデーション**: バックエンドが特定のファイル形式のみを期待している可能性

#### 🔍 422エラーの発生箇所

line 57-61のログから：
```
POST http://localhost:8000/api/snapshots 422 (Unprocessable Entity)
```

**重要**: バックエンドのログが提供されていないため、FastAPIのバリデーションエラーの詳細が不明です。

### 追加の問題

**line 8**: 正規表現の警告（すでに修正済み）
```
Pattern attribute value [a-zA-Z0-9_-]+ is not a valid regular expression
```

これは直接の422エラーの原因ではありませんが、修正しました。

## 実施した修正

### 1. フロントエンド: 正規表現の修正

**ファイル**: `frontend/src/components/SnapshotUpload.js`

**変更前**:
```html
pattern="[a-zA-Z0-9_-]+"
```

**変更後**:
```html
pattern="[a-zA-Z0-9_\-]+"
```

ハイフン `-` をエスケープして、ブラウザの警告を解消しました。

### 2. バックエンド: 422エラーの詳細ログを追加

**ファイル**: `backend/src/main.py`

**追加内容**:
- `RequestValidationError` の例外ハンドラーを追加
- FastAPIのバリデーションエラーを詳細にログ出力
- エラーレスポンスに`details`配列を含める

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(
        "Request validation error (422)",
        extra={
            "url": str(request.url),
            "method": request.method,
            "errors": exc.errors(),
            "body": exc.body if hasattr(exc, 'body') else None
        }
    )

    # Log detailed error information
    for error in exc.errors():
        logger.error(
            f"Validation error detail",
            extra={
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "type": error.get("type"),
                "input": error.get("input")
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request validation failed",
            "code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )
```

これにより、以下の情報がバックエンドログに出力されるようになります：
- バリデーションエラーが発生したフィールド (`loc`)
- エラーメッセージ (`msg`)
- エラータイプ (`type`)
- 入力値 (`input`)

### 3. フロントエンド: 422エラー時の詳細表示

**ファイル**: `frontend/src/components/SnapshotUpload.js`

**追加内容**:
- 422エラー時に詳細なメッセージを表示
- バリデーションエラーの詳細をコンソールに出力

```javascript
} else if (error.status === 422) {
  errorMessage = 'Invalid request. Please check the error details in browser console.';
  // Log detailed validation errors
  if (error.details) {
    console.error('[VALIDATION ERROR] Details:', error.details);
    console.error('[VALIDATION ERROR] Please check:');
    console.error('  1. All files are valid network configuration files');
    console.error('  2. Snapshot name contains only alphanumeric, hyphen, underscore');
    console.error('  3. Files are not corrupted or empty');
  }
}
```

## 次に実施してほしいこと

### 手順1: バックエンドを再起動

WSL Ubuntuターミナルで：

```bash
# 現在のバックエンドを停止（Ctrl+C）

cd ~/batfish_vis/backend
source .venv/bin/activate

# LOG_LEVELをDEBUGに設定（.envファイル）
cat > .env << EOF
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=DEBUG
EOF

# バックエンドを再起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 手順2: フロントエンドを再起動

Windows PowerShellで：

```powershell
# 現在のフロントエンドを停止（Ctrl+C）

cd D:\batfish_vis\frontend

# ブラウザキャッシュ対策: distを削除
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue

# 再起動
npm run dev
```

### 手順3: ブラウザでテスト

1. ブラウザで **http://localhost:5173** にアクセス
2. **F12** → **Console** タブを開く
3. コンソールをクリア

4. **重要: .cfgファイルのみを選択してテスト**

   まず、画像ファイルなどを除外してテストします：

   a. **Select Files** を選択（フォルダではなくファイルモード）
   b. `D:\networks\example` フォルダを開く
   c. **Ctrl+クリック** で `.cfg` ファイル**のみ**を選択：
      - as1border1.cfg
      - as1border2.cfg
      - as1core1.cfg
      - as2border1.cfg
      - as2border2.cfg
      - as2core1.cfg
      - as2core2.cfg
      - as2dept1.cfg
      - as2dist1.cfg
      - as2dist2.cfg
      - as3border1.cfg
      - as3border2.cfg
      - as3core1.cfg
   d. **開く** をクリック
   e. Snapshot Name: `test-config-only`
   f. **Create Snapshot** をクリック

### 手順4: ログを確認

#### A. ブラウザコンソール

期待されるログ:
```
[DEBUG] selectedFiles.length: 13
[DEBUG] Form submission starting
[DEBUG] createSnapshot called with: { fileCount: 13 }
```

422エラーが出た場合:
```
[VALIDATION ERROR] Details: [...]
[VALIDATION ERROR] Please check:
  1. All files are valid network configuration files
  2. Snapshot name contains only alphanumeric, hyphen, underscore
  3. Files are not corrupted or empty
```

#### B. バックエンドログ（WSL Ubuntuターミナル）

**成功する場合**:
```
INFO: Snapshot creation request received
  snapshot: test-config-only
  network: default
  file_count: 13
  files: ['as1border1.cfg', 'as1border2.cfg', ...]
```

**422エラーが出る場合**:
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

### 手順5: 結果を報告

以下の情報を報告してください：

#### A. テスト結果

- .cfgファイルのみ選択: 成功 / 失敗

#### B. ブラウザコンソールログ

`[DEBUG]` と `[VALIDATION ERROR]` で始まる行をすべてコピー

#### C. バックエンドログ

WSL Ubuntuターミナルに表示された**すべてのログ**をコピー

特に以下が重要：
- `Request validation error (422)` で始まる行
- `Validation error detail` で始まる行

## 予想される結果

### シナリオ1: .cfgファイルのみで成功

→ **原因**: 画像ファイルや.json/.iptablesファイルがバックエンドで拒否されている

**対策**: フォルダアップロード時に、特定のファイル形式のみをフィルタリングする機能を追加

### シナリオ2: .cfgファイルのみでも422エラー

→ **原因**: ファイル内容、ファイル名、またはバックエンドのバリデーションロジックに問題がある

**対策**: バックエンドログの詳細を確認して、具体的なバリデーションエラーを特定

### シナリオ3: バックエンドログに何も表示されない

→ **原因**: バックエンドがリクエストを受信していない、またはCORS/ネットワークの問題

**対策**:
- ブラウザのNetworkタブでリクエストの詳細を確認
- curlで直接バックエンドをテスト

## Batfishのフォルダ構造について

Batfishは以下のようなフォルダ構造をサポートしています：

### 標準構造（推奨）

```
snapshot/
├── configs/
│   ├── router1.cfg
│   ├── router2.cfg
│   └── switch1.cfg
└── hosts/
    ├── host1.json
    ├── host2.json
    ├── host1.iptables
    └── host2.iptables
```

### フラット構造（現在のアップロード）

```
snapshot/
├── router1.cfg
├── router2.cfg
├── switch1.cfg
├── host1.json
├── host2.json
├── host1.iptables
└── host2.iptables
```

Batfish自体は両方の構造をサポートしていますが、**画像ファイル（.png）はサポートしていません**。

## まとめ

**修正内容**:
1. ✅ フロントエンド: 正規表現の警告を修正
2. ✅ バックエンド: 422エラーの詳細ログを追加
3. ✅ フロントエンド: 422エラー時の詳細表示を追加

**次のステップ**:
1. バックエンドとフロントエンドを再起動
2. .cfgファイル**のみ**を選択してテスト
3. バックエンドログとブラウザコンソールログを報告

**予想される原因**:
- 画像ファイル（example-network.png）がバリデーションエラーを引き起こしている
- または、.iptables/.jsonファイルがバックエンドで拒否されている

バックエンドログを確認することで、正確な原因を特定できます。
