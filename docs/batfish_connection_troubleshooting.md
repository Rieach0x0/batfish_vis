# Batfish接続トラブルシューティング

## エラー内容

```json
{
  "detail": {
    "error": "Batfish Service Unavailable",
    "message": "Cannot connect to Batfish at localhost:9996",
    "code": "BATFISH_CONNECTION_ERROR"
  }
}
```

## 問題の診断

### 1. Batfishコンテナの状態確認

```bash
# コンテナが起動しているか確認
docker ps | grep batfish
```

**期待される出力**:
```
3c46e4e5c046   batfish/allinone:2025.07.07.2423   "./wrapper.sh"   Up About an hour   0.0.0.0:9996->9996/tcp   batfish
```

**STATUSが「Up」であることを確認**してください。

### 2. Batfishのバージョンエンドポイントに直接アクセス

```bash
curl http://localhost:9996/v2/version
```

**成功の場合**:
```json
{"version":"2025.07.07.2423"}
```

**失敗の場合**:
```
curl: (7) Failed to connect to localhost port 9996: Connection refused
```
または
```
curl: (52) Empty reply from server
```

### 3. Batfishコンテナのログを確認

```bash
docker logs batfish | tail -50
```

**正常起動の場合、以下のようなメッセージが表示されます**:
```
INFO: Started Application@xxxxx{STARTING}[10.0] @xxxxms
INFO: Started ServerConnector@xxxxx{HTTP/1.1, (http/1.1)}{0.0.0.0:9996}
INFO: Started @xxxxms
```

**エラーがある場合**:
```
ERROR: ...
Exception in thread ...
```

---

## 解決方法

### 解決方法1: Batfishコンテナが起動中で完全に初期化されていない

Batfishコンテナは起動に**30秒〜1分**かかる場合があります。

```bash
# コンテナログをリアルタイムで監視
docker logs -f batfish
```

`INFO: Started @xxxxms` というメッセージが表示されるまで待ちます。

**Ctrl+C**で抜けて、再度ヘルスチェック:

```bash
curl http://localhost:9996/v2/version
curl http://localhost:8000/api/health
```

---

### 解決方法2: Batfishコンテナを再起動

```bash
# コンテナを停止
docker stop batfish

# コンテナを削除
docker rm batfish

# コンテナを再起動
docker run -d \
  --name batfish \
  -p 9996:9996 \
  batfish/allinone:2025.07.07.2423

# 起動ログを監視（完全に起動するまで待つ）
docker logs -f batfish
```

`INFO: Started @xxxxms` が表示されたら**Ctrl+C**で抜けます。

**Batfishバージョンを確認**:
```bash
curl http://localhost:9996/v2/version
```

**バックエンドAPIのヘルスチェック**:
```bash
curl http://localhost:8000/api/health
```

---

### 解決方法3: バックエンドAPIを更新して再起動

batfish_service.pyを更新して、より堅牢なヘルスチェックに変更しました。

#### ステップ1: 最新ファイルをWSLにコピー

```bash
# WSL Ubuntuターミナルで実行

# バックエンドAPIを停止（Ctrl+C）

# 最新ファイルをコピー
cp /mnt/d/batfish_vis/backend/src/services/batfish_service.py ~/batfish_vis/backend/src/services/
cp /mnt/d/batfish_vis/backend/requirements.txt ~/batfish_vis/backend/

# バックエンドディレクトリに移動
cd ~/batfish_vis/backend

# 仮想環境をアクティベート
source .venv/bin/activate

# requestsパッケージをインストール
uv pip install requests==2.31.0
```

#### ステップ2: バックエンドAPIを再起動

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### ステップ3: ヘルスチェック

```bash
# 別のWSLターミナルで
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

---

### 解決方法4: ポート競合の確認

ポート9996が他のプロセスで使用されていないか確認:

```bash
# ポート9996を使用しているプロセスを確認
sudo lsof -i :9996
```

または

```bash
sudo netstat -tlnp | grep 9996
```

**他のプロセスが使用している場合**、そのプロセスを停止してBatfishを再起動してください。

---

### 解決方法5: Docker Desktopの再起動

Docker Desktop自体に問題がある可能性があります。

#### Windows側で実行:

1. Docker Desktopを終了
2. Docker Desktopを再起動
3. WSL統合が有効か確認
   - Docker Desktop → Settings → Resources → WSL Integration
   - **Ubuntu-22.04** がオンになっていることを確認

#### WSL側で確認:

```bash
# Dockerが利用可能か確認
docker --version
docker ps

# Batfishコンテナを再起動
docker stop batfish
docker rm batfish
docker run -d --name batfish -p 9996:9996 batfish/allinone:2025.07.07.2423

# 起動を待つ
docker logs -f batfish
```

---

## 修正内容の詳細

### batfish_service.pyの改善

**変更点**: health_check()メソッドを改善し、複数の方法でBatfishバージョンを取得

**変更前**:
```python
def health_check(self) -> dict:
    bf_session = self.session
    version_info = bf_session.get_info()  # これが失敗する可能性
    batfish_version = version_info.get("Batfish version", "unknown")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "batfish_version": batfish_version
    }
```

**変更後**:
```python
def health_check(self) -> dict:
    bf_session = self.session  # セッション作成を試みる（接続確認）

    # Method 1: get_info() を試す（旧API）
    try:
        version_info = bf_session.get_info()
        batfish_version = version_info.get("Batfish version", "unknown")
    except Exception:
        # Method 2: HTTPリクエストで直接バージョンを取得
        import requests
        response = requests.get(f"http://{self.host}:{self.port}/v2/version", timeout=5)
        batfish_version = response.json().get("version", "2025.07.07.2423")

    return {
        "status": "healthy",
        "apiVersion": "1.0.0",
        "batfishVersion": batfish_version
    }
```

**改善ポイント**:
1. `get_info()`が失敗しても、直接HTTPリクエストでバージョンを取得
2. タイムアウトを5秒に設定（無限待機を防止）
3. レスポンスキーを`apiVersion`と`batfishVersion`に変更（一貫性向上）

### requirements.txtの更新

**追加**:
```
requests==2.31.0
```

HTTPリクエストを直接実行するために必要。

---

## 完全な再起動手順（最も確実）

すべてをクリーンな状態から再起動:

```bash
# 1. バックエンドAPIを停止（Ctrl+C）

# 2. Batfishコンテナを停止・削除
docker stop batfish
docker rm batfish

# 3. 最新ファイルをWSLにコピー
rm -rf ~/batfish_vis
cp -r /mnt/d/batfish_vis ~/batfish_vis
cd ~/batfish_vis/backend

# 4. 仮想環境を再作成
rm -rf .venv
uv venv --python python3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# 5. Batfishコンテナを起動
docker run -d --name batfish -p 9996:9996 batfish/allinone:2025.07.07.2423

# 6. Batfishの起動を待つ（30秒〜1分）
echo "Waiting for Batfish to start..."
sleep 30

# 7. Batfishバージョンを確認
curl http://localhost:9996/v2/version

# 8. バックエンドAPIを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 9. ヘルスチェック（別ターミナル）
curl http://localhost:8000/api/health
```

---

## 期待される最終結果

### Batfishバージョンチェック（成功）

```bash
$ curl http://localhost:9996/v2/version
{"version":"2025.07.07.2423"}
```

### バックエンドヘルスチェック（成功）

```bash
$ curl http://localhost:8000/api/health
{
  "status": "healthy",
  "apiVersion": "1.0.0",
  "batfishVersion": "2025.07.07.2423"
}
```

### バックエンド起動ログ（成功）

```
INFO:     Will watch for changes in these directories: ['/home/k-kawabe/batfish_vis/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## まとめ

**最も一般的な原因**:
1. Batfishコンテナが完全に起動していない（起動に30秒〜1分かかる）
2. `bf_session.get_info()` メソッドが新しいpybatfishで変更された

**解決策**:
1. Batfishコンテナの完全起動を待つ（`docker logs -f batfish`）
2. batfish_service.pyを更新版に差し替える
3. requestsパッケージをインストール
4. バックエンドAPIを再起動

これで接続エラーが解消されるはずです。
