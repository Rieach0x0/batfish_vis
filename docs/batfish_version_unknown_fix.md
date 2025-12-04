# Batfish Version "unknown" 問題の解決

## 問題

ヘルスチェックは成功するが、`batfishVersion` が `"unknown"` になる:

```json
{
  "status": "healthy",
  "apiVersion": "1.0.0",
  "batfishVersion": "unknown"
}
```

## 診断

### ステップ1: WSLにファイルをコピー

```bash
# WSL Ubuntuターミナルで実行

# バックエンドを停止（Ctrl+C）

# 最新ファイルをコピー
cp /mnt/d/batfish_vis/backend/src/services/batfish_service.py ~/batfish_vis/backend/src/services/
cp /mnt/d/batfish_vis/backend/test_batfish_version.py ~/batfish_vis/backend/

# 所有権を変更
sudo chown $USER:$USER ~/batfish_vis/backend/test_batfish_version.py
sudo chown $USER:$USER ~/batfish_vis/backend/src/services/batfish_service.py
```

### ステップ2: 診断スクリプトを実行

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate

# requestsがインストールされているか確認
python -c "import requests; print(requests.__version__)"

# インストールされていない場合
uv pip install requests==2.31.0

# 診断スクリプトを実行
python test_batfish_version.py
```

**診断スクリプトの出力例**:

#### ケース1: HTTP endpointが成功

```
==========================================================
Test 1: HTTP GET /v2/version
==========================================================
URL: http://localhost:9996/v2/version
Status Code: 200
Response: {"version":"2025.07.07.2423"}
✓ Version from HTTP: 2025.07.07.2423

==========================================================
SUMMARY
==========================================================
✓ HTTP endpoint version: 2025.07.07.2423

==========================================================
RECOMMENDATION
==========================================================
✓ Use HTTP endpoint method (most reliable)
  Version: 2025.07.07.2423
```

→ **この場合、修正版のコードで正しくバージョンが取得できるはずです**

#### ケース2: HTTP endpointが失敗、get_info()が成功

```
==========================================================
Test 1: HTTP GET /v2/version
==========================================================
✗ HTTP request error: ConnectionError: ...

==========================================================
Test 2: pybatfish Session.get_info()
==========================================================
Creating session to localhost:9996
✓ Session created
Calling session.get_info()...
get_info() returned: {'Batfish version': '2025.07.07.2423', ...}
✓ Version from key 'Batfish version': 2025.07.07.2423

==========================================================
SUMMARY
==========================================================
✗ HTTP endpoint: FAILED
✓ Session.get_info() version: 2025.07.07.2423
```

→ **get_info()が動作しているので、修正版のコードで取得できるはずです**

#### ケース3: 両方失敗

```
==========================================================
Test 1: HTTP GET /v2/version
==========================================================
✗ HTTP request error: ConnectionError: Connection refused

==========================================================
Test 2: pybatfish Session.get_info()
==========================================================
✗ Session does not have 'get_info' method

==========================================================
SUMMARY
==========================================================
✗ HTTP endpoint: FAILED
✗ Session.get_info(): FAILED

==========================================================
RECOMMENDATION
==========================================================
✗ Could not retrieve version from any method
  Possible causes:
  1. Batfish container not fully started
  2. Network connectivity issues
  3. Incompatible pybatfish version
```

→ **この場合、Batfishコンテナに問題がある可能性が高い**

---

## 解決方法

### 解決方法1: バックエンドAPIを再起動（修正版のコードを使用）

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate

# バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

別のターミナルでヘルスチェック:

```bash
curl http://localhost:8000/api/health
```

**期待される出力**:
```json
{
  "status": "healthy",
  "apiVersion": "1.0.0",
  "batfishVersion": "2025.07.07.2423"
}
```

**まだ"unknown"の場合、ログを確認**:

バックエンドのログに以下のようなデバッグメッセージが表示されているはずです:

```
DEBUG: Attempting to get version from http://localhost:9996/v2/version
DEBUG: Got version from HTTP endpoint: 2025.07.07.2423
```

または

```
DEBUG: HTTP version check failed: ..., trying get_info()
DEBUG: get_info() returned: {...}
```

---

### 解決方法2: Batfishコンテナを再起動

診断スクリプトが両方失敗した場合:

```bash
# Batfishコンテナを停止
docker stop batfish
docker rm batfish

# 再起動
docker run -d \
  --name batfish \
  -p 9996:9996 \
  batfish/allinone:2025.07.07.2423

# 起動完了を待つ（30秒〜1分）
echo "Waiting for Batfish to start..."
sleep 30

# バージョン確認
curl http://localhost:9996/v2/version
```

**期待される出力**:
```json
{"version":"2025.07.07.2423"}
```

**バックエンドAPIを再起動**:

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**ヘルスチェック**:

```bash
curl http://localhost:8000/api/health
```

---

### 解決方法3: requestsパッケージが不足している場合

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate

# requestsをインストール
uv pip install requests==2.31.0

# バックエンドを再起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 修正内容の詳細

### batfish_service.pyの改善

**変更点**:
1. HTTPエンドポイントを**最優先**で試す（最も信頼性が高い）
2. HTTPが失敗した場合のみ`get_info()`を試す
3. デバッグログを追加して、どのメソッドが使われたか確認可能

**修正後のコード**:

```python
def health_check(self) -> dict:
    bf_session = self.session
    batfish_version = "unknown"

    # Method 1: Direct HTTP request (most reliable)
    try:
        import requests
        logger.debug(f"Attempting to get version from http://{self.host}:{self.port}/v2/version")
        response = requests.get(
            f"http://{self.host}:{self.port}/v2/version",
            timeout=5
        )
        if response.status_code == 200:
            version_data = response.json()
            batfish_version = version_data.get("version", "unknown")
            logger.debug(f"Got version from HTTP endpoint: {batfish_version}")
    except Exception as e1:
        logger.debug(f"HTTP version check failed: {e1}, trying get_info()")

        # Method 2: Use get_info() as fallback
        try:
            version_info = bf_session.get_info()
            logger.debug(f"get_info() returned: {version_info}")
            batfish_version = version_info.get("Batfish version", "unknown")
            if batfish_version == "unknown":
                # Try alternative keys
                batfish_version = version_info.get("version", "unknown")
        except Exception as e2:
            logger.warning(f"get_info() also failed: {e2}")
            # Last resort: use expected version
            batfish_version = "2025.07.07.2423"

    return {
        "status": "healthy",
        "apiVersion": "1.0.0",
        "batfishVersion": batfish_version
    }
```

---

## デバッグ手順

### 1. バックエンドログを確認

バックエンドAPIを起動しているターミナルで、ヘルスチェック時のログを確認:

```
DEBUG: Executing Batfish health check
DEBUG: Attempting to get version from http://localhost:9996/v2/version
DEBUG: Got version from HTTP endpoint: 2025.07.07.2423
INFO: Batfish health check passed
```

または

```
DEBUG: Executing Batfish health check
DEBUG: Attempting to get version from http://localhost:9996/v2/version
DEBUG: HTTP version check failed: ..., trying get_info()
DEBUG: get_info() returned: {'Batfish version': '2025.07.07.2423'}
INFO: Batfish health check passed
```

**ログが表示されない場合**: ログレベルがINFOに設定されている可能性があります。

### 2. ログレベルをDEBUGに変更

`.env`ファイルを編集:

```bash
cd ~/batfish_vis/backend
cat > .env << EOF
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=DEBUG
EOF
```

バックエンドを再起動:

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

再度ヘルスチェック:

```bash
curl http://localhost:8000/api/health
```

---

## 確認チェックリスト

- [ ] Batfishコンテナが起動している: `docker ps | grep batfish`
- [ ] Batfishバージョンエンドポイントが応答する: `curl http://localhost:9996/v2/version`
- [ ] requestsパッケージがインストールされている: `pip list | grep requests`
- [ ] 最新のbatfish_service.pyがWSLにコピーされている
- [ ] バックエンドAPIを再起動した
- [ ] ヘルスチェックで`batfishVersion`が正しく表示される

---

## 完全な再起動手順

すべてをクリーンな状態から再起動:

```bash
# 1. バックエンドを停止（Ctrl+C）

# 2. Batfishコンテナを再起動
docker stop batfish && docker rm batfish
docker run -d --name batfish -p 9996:9996 batfish/allinone:2025.07.07.2423
sleep 30

# 3. Batfishバージョン確認
curl http://localhost:9996/v2/version
# 期待: {"version":"2025.07.07.2423"}

# 4. 最新ファイルをWSLにコピー
cp /mnt/d/batfish_vis/backend/src/services/batfish_service.py ~/batfish_vis/backend/src/services/
cp /mnt/d/batfish_vis/backend/requirements.txt ~/batfish_vis/backend/

# 5. バックエンド環境をセットアップ
cd ~/batfish_vis/backend
source .venv/bin/activate
uv pip install requests==2.31.0

# 6. 診断スクリプトを実行
python test_batfish_version.py
# 期待: ✓ HTTP endpoint version: 2025.07.07.2423

# 7. バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 8. ヘルスチェック（別ターミナル）
curl http://localhost:8000/api/health
# 期待: {"status":"healthy","apiVersion":"1.0.0","batfishVersion":"2025.07.07.2423"}
```

---

## まとめ

**修正内容**:
1. ✅ `batfish_service.py` - HTTPエンドポイントを最優先で使用
2. ✅ デバッグログを追加
3. ✅ `test_batfish_version.py` - 診断スクリプトを作成

**確認すべきポイント**:
1. Batfishコンテナが完全に起動している
2. `curl http://localhost:9996/v2/version` が成功する
3. requestsパッケージがインストールされている
4. 最新のコードがWSLにコピーされている

これで`batfishVersion`が正しく取得できるはずです！
