# WSL Ubuntu セットアップガイド - Batfish Visualization

このガイドでは、WSL Ubuntu上でBatfishコンテナとバックエンドAPIを動作させ、Windows上でフロントエンドを実行する手順を説明します。

## 前提条件

### Windows環境
- Windows 10/11 (WSL2対応バージョン)
- Docker Desktop for Windows (WSL2バックエンド有効)
- Node.js 18+ (Windows上にインストール)
- Windows Terminal (推奨)

### WSL環境
- Ubuntu 22.04 LTS (WSL2)
- uv (Python環境管理ツール)
- Docker (Docker Desktopから利用)

---

## 1. WSL Ubuntuのセットアップ

### 1.1 WSL2のインストール

PowerShellを管理者権限で開き、以下を実行:

```powershell
# WSL2とUbuntuをインストール
wsl --install -d Ubuntu-22.04

# WSL2がデフォルトバージョンであることを確認
wsl --set-default-version 2

# インストール後、Ubuntuを起動してユーザー名とパスワードを設定
```

### 1.2 WSLの確認

```powershell
# インストールされているディストリビューションを確認
wsl --list --verbose

# 出力例:
#   NAME            STATE           VERSION
# * Ubuntu-22.04    Running         2
```

### 1.3 Docker Desktop WSL2統合

1. Docker Desktop for Windowsを起動
2. **Settings** → **Resources** → **WSL Integration**
3. **Enable integration with my default WSL distro** をオン
4. **Ubuntu-22.04** をオン
5. **Apply & Restart**

### 1.4 WSL Ubuntuでの動作確認

WSL Ubuntuターミナルを開き:

```bash
# Dockerが利用可能か確認
docker --version
# 出力例: Docker version 24.0.7, build afdd53b

# Dockerが動作するか確認
docker ps
```

---

## 2. Python環境のセットアップ (WSL Ubuntu)

### 2.1 システムパッケージの更新

```bash
# システムパッケージを更新
sudo apt update && sudo apt upgrade -y

# 必要なビルドツール
sudo apt install -y build-essential curl
```

### 2.2 Python 3.11+のインストール

Python 3.11以上が必要です。

```bash
# Python 3.11をインストール
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Pythonバージョン確認
python3.11 --version
# 出力例: Python 3.11.7

# python3をpython3.11にリンク（オプション、推奨）
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --config python3
# python3.11を選択

# 確認
python3 --version
# 出力例: Python 3.11.7
```

### 2.3 uvのインストール

uvは高速なPythonパッケージマネージャーで、venvよりも高速に環境構築ができます。

```bash
# uvをインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# シェルを再起動して環境変数を反映
source $HOME/.cargo/env

# uvのバージョン確認
uv --version
# 出力例: uv 0.4.x

# uvがPATHに追加されていることを確認
which uv
# 出力例: /home/<username>/.cargo/bin/uv
```

**注意**: uvのインストールスクリプトは `~/.cargo/bin/` にuvをインストールし、`~/.bashrc` または `~/.profile` にPATHを追加します。

---

## 3. プロジェクトファイルのセットアップ

### オプションA: Windows側のファイルを直接参照 (簡単だが低速)

```bash
# WSLからWindowsのDドライブにアクセス
cd /mnt/d/batfish_vis
```

**注意**: `/mnt/`経由のファイルアクセスはI/O性能が低下します。

### オプションB: WSLホームディレクトリにコピー (推奨)

```bash
# プロジェクトファイルをWSLにコピー
cp -r /mnt/d/batfish_vis ~/batfish_vis

# 移動
cd ~/batfish_vis

# 所有権を変更（権限エラー回避）
sudo chown -R $USER:$USER ~/batfish_vis
```

**推奨**: WSLホームディレクトリにコピーすることで、Linuxネイティブのファイルシステム性能を利用できます。

---

## 4. Batfishコンテナの起動 (WSL Ubuntu)

```bash
# Batfishコンテナを起動
docker run -d \
  --name batfish \
  -p 9996:9996 \
  batfish/allinone:2025.07.07.2423

# コンテナが起動したか確認
docker ps | grep batfish

# Batfishバージョン確認
curl http://localhost:9996/v2/version
```

**出力例**:
```json
{"version":"2025.07.07"}
```

---

## 5. バックエンドAPIの起動 (WSL Ubuntu)

```bash
cd ~/batfish_vis/backend

# uvでPython 3.11環境を作成（pyproject.tomlでPython 3.11+が必須）
# uvは自動的に仮想環境を作成し、Python 3.11+を使用します
uv venv --python python3.11

# 仮想環境をアクティベート
source .venv/bin/activate

# Pythonバージョン確認（Python 3.11+であることを確認）
python --version
# 出力例: Python 3.11.7

# 依存パッケージをuvで高速インストール
uv pip install -r requirements.txt

# .envファイルを作成（オプション）
cat > .env << EOF
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=INFO
EOF

# バックエンドAPIを起動 (重要: --host 0.0.0.0 でWindows側からアクセス可能にする)
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**uvの利点**:
- `uv pip install` は `pip install` よりも10-100倍高速
- `uv venv` でPythonバージョンを自動検出して仮想環境を作成
- `uv run` でコマンドを仮想環境内で直接実行可能

**重要**: `--host 0.0.0.0` を指定することで、WSL外部(Windows側)からAPIにアクセスできます。

**動作確認** (Windows PowerShellまたはWSL Ubuntuから):

```bash
# ヘルスチェック
curl http://localhost:8000/api/health
```

**出力例**:
```json
{
  "status": "healthy",
  "batfishVersion": "2025.07.07",
  "apiVersion": "1.0.0"
}
```

---

## 6. フロントエンドの起動 (Windows)

**Windows PowerShell**を開き:

```powershell
# プロジェクトディレクトリに移動
cd D:\batfish_vis\frontend

# 依存パッケージをインストール（初回のみ）
npm install

# .envファイルを作成（オプション）
@"
VITE_API_URL=http://localhost:8000/api
"@ | Out-File -FilePath .env -Encoding utf8

# 開発サーバーを起動
npm run dev
```

**出力例**:
```
  VITE v4.5.0  ready in 523 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 7. ブラウザでアクセス (Windows)

Windowsのブラウザで以下にアクセス:

```
http://localhost:5173
```

**アプリケーションが表示されれば成功です！**

---

## 8. 使用方法

### 8.1 スナップショットの作成

1. **Upload Configuration Files** セクションで設定ファイルを選択
2. **Snapshot Name** と **Network Name** を入力
3. **Upload Snapshot** をクリック

### 8.2 トポロジーの表示

1. スナップショット一覧から作成したスナップショットを選択
2. トポロジーグラフが自動的に表示されます
3. ノードやリンクにカーソルを当てると詳細情報が表示されます

### 8.3 検証クエリの実行

1. **Verification** タブを開く
2. クエリタイプを選択 (Reachability / ACL / Routing)
3. パラメータを入力して **Run Query** をクリック

---

## 9. WSL固有のトラブルシューティング

### 9.1 Dockerが見つからない

**症状**: `docker: command not found`

**解決方法**:
```bash
# Docker Desktop for Windowsが起動しているか確認
# Windows側で Docker Desktop を起動

# Docker Desktop設定でWSL統合を有効化
# Settings → Resources → WSL Integration → Ubuntu-22.04 をオン
```

### 9.2 Windows側からWSLのバックエンドにアクセスできない

**症状**: フロントエンドが `localhost:8000` に接続できない

**解決方法**:
```bash
# バックエンドが 0.0.0.0 でリッスンしているか確認
# 起動コマンドに --host 0.0.0.0 が含まれていることを確認
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# WSLのIPアドレスを確認（WSL側）
hostname -I
# 出力例: 172.25.240.123

# Windows側からWSLのIPで直接アクセス可能
curl http://172.25.240.123:8000/api/health
```

**注意**: WSL2では通常、`localhost` でWSLサービスにアクセス可能です。

### 9.3 ファイル権限エラー

**症状**: `Permission denied` エラー

**解決方法**:
```bash
# プロジェクトディレクトリの所有権を変更
sudo chown -R $USER:$USER ~/batfish_vis

# 実行権限を付与（スクリプトファイルの場合）
chmod +x ~/batfish_vis/*.sh
```

### 9.4 uvコマンドが見つからない

**症状**: `uv: command not found`

**解決方法**:
```bash
# uvのインストール状態を確認
which uv

# uvが見つからない場合は再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 環境変数を再読み込み
source $HOME/.cargo/env

# または、シェルを再起動
exec $SHELL

# .bashrcまたは.profileにPATHが追加されているか確認
cat ~/.bashrc | grep cargo
# 出力例: export PATH="$HOME/.cargo/bin:$PATH"
```

### 9.5 Python 3.10が使用されている

**症状**: エラーログに `python3.10` が表示される、または `requires-python >=3.11` の警告

**解決方法**:
```bash
# Python 3.11がインストールされているか確認
python3.11 --version

# インストールされていない場合
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# 既存の仮想環境を削除
cd ~/batfish_vis/backend
rm -rf .venv

# Python 3.11で仮想環境を再作成
uv venv --python python3.11
source .venv/bin/activate

# Pythonバージョン確認
python --version
# 出力: Python 3.11.7

# 依存パッケージを再インストール
uv pip install -r requirements.txt
```

### 9.6 uv venvで仮想環境作成に失敗

**症状**: `uv venv` で仮想環境が作成できない

**解決方法**:
```bash
# uvを最新バージョンに更新
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Pythonが利用可能か確認
python3.11 --version

# 明示的にPythonバージョンを指定して仮想環境を作成
uv venv --python python3.11
```

### 9.7 pybatfishのインポートエラー

**症状**: `ImportError: cannot import name 'bfq' from 'pybatfish.question'`

**原因**: pybatfish 2025.7.7以降でAPIが変更されました

**解決方法**:
このエラーは既に修正されています。最新のコードを取得してください:
```bash
# プロジェクトを最新化
cd ~/batfish_vis
git pull  # Gitを使用している場合

# または、Windows側から再度コピー
rm -rf ~/batfish_vis
cp -r /mnt/d/batfish_vis ~/batfish_vis

# 仮想環境を再作成
cd ~/batfish_vis/backend
rm -rf .venv
uv venv --python python3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 9.8 WSL IPアドレスの取得

```bash
# WSL側から
hostname -I

# Windows PowerShell側から
wsl hostname -I
```

---

## 10. 起動・停止スクリプト

### 10.1 起動スクリプト (`~/batfish_vis/start.sh`)

```bash
#!/bin/bash

echo "========================================="
echo "  Batfish Visualization - WSL Startup"
echo "========================================="

echo ""
echo "[1/2] Starting Batfish container..."
if docker ps | grep -q batfish; then
    echo "  ✓ Batfish container already running"
else
    docker start batfish 2>/dev/null || \
    docker run -d --name batfish -p 9996:9996 batfish/allinone:2025.07.07.2423
    echo "  ✓ Batfish container started"
fi

echo ""
echo "[2/2] Waiting for Batfish to be ready..."
sleep 5
curl -s http://localhost:9996/v2/version > /dev/null && echo "  ✓ Batfish is ready"

echo ""
echo "========================================="
echo "  Backend API Starting..."
echo "========================================="
cd ~/batfish_vis/backend

# uvで仮想環境をアクティベート（存在しない場合は作成）
if [ ! -d ".venv" ]; then
    echo "Creating Python 3.11 virtual environment with uv..."
    uv venv --python python3.11
    source .venv/bin/activate
    echo "Python version: $(python --version)"
    echo "Installing dependencies with uv..."
    uv pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo ""
echo "Backend API listening on http://0.0.0.0:8000"
echo "Accessible from Windows at http://localhost:8000"
echo ""
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 10.2 停止スクリプト (`~/batfish_vis/stop.sh`)

```bash
#!/bin/bash

echo "========================================="
echo "  Batfish Visualization - WSL Shutdown"
echo "========================================="

echo ""
echo "Stopping Batfish container..."
docker stop batfish 2>/dev/null && echo "  ✓ Batfish container stopped" || echo "  - Batfish container not running"

echo ""
echo "Backend API stopped (Ctrl+C in the terminal)"
echo ""
echo "========================================="
```

### 10.3 スクリプトに実行権限を付与

```bash
chmod +x ~/batfish_vis/start.sh
chmod +x ~/batfish_vis/stop.sh
```

### 10.4 使用方法

```bash
# 起動（WSL Ubuntu）
~/batfish_vis/start.sh

# 停止（WSL Ubuntu - 別ターミナル）
~/batfish_vis/stop.sh
```

---

## 11. Windows Terminal設定（推奨）

Windows Terminalで3つのタブを開いて作業すると便利です:

### タブ1: WSL - Batfish & Backend
```bash
~/batfish_vis/start.sh
```

### タブ2: Windows PowerShell - Frontend
```powershell
cd D:\batfish_vis\frontend
npm run dev
```

### タブ3: WSL - 作業用
```bash
cd ~/batfish_vis
# 各種コマンド実行やログ確認など
```

---

## 12. 開発ワークフロー

### 日常的な起動手順

1. **Windows Terminal** を開く
2. **タブ1 (WSL Ubuntu)**: `~/batfish_vis/start.sh` を実行
3. **タブ2 (Windows PowerShell)**: `npm run dev` を実行
4. **ブラウザ**: `http://localhost:5173` にアクセス

### 停止手順

1. **タブ2**: `Ctrl + C` でフロントエンドを停止
2. **タブ1**: `Ctrl + C` でバックエンドを停止
3. **タブ3 (WSL)**: `~/batfish_vis/stop.sh` でBatfishコンテナを停止

---

## 13. API動作確認

### ヘルスチェック

```bash
curl http://localhost:8000/api/health
```

### スナップショット一覧

```bash
curl http://localhost:8000/api/snapshots
```

### トポロジー取得

```bash
curl "http://localhost:8000/api/topology?snapshot=test-network&network=default"
```

---

## 14. ログとデバッグ

### Batfishコンテナログ

```bash
docker logs batfish
docker logs -f batfish  # リアルタイム表示
```

### バックエンドAPIログ

バックエンド起動ターミナルに直接出力されます。

### フロントエンドログ

- ブラウザのデベロッパーツール (F12) → Console

---

## 15. パフォーマンス最適化

### ファイルI/O性能

- **推奨**: WSLホームディレクトリ (`~/batfish_vis`) でプロジェクトを実行
- **避ける**: `/mnt/d/` 経由でのアクセス (クロスファイルシステムは低速)

### Python環境構築の高速化

**uvを使用したパッケージインストール**:
```bash
# 従来のpip (遅い)
time pip install -r requirements.txt
# 実行時間例: 約60秒

# uvを使用 (高速)
time uv pip install -r requirements.txt
# 実行時間例: 約3-5秒 (10-20倍高速)
```

**uvキャッシュの活用**:
- uvは自動的にパッケージをキャッシュします
- 2回目以降のインストールはさらに高速化
- キャッシュクリア: `uv cache clean`

### Dockerリソース

Docker Desktopで割り当てるリソースを調整:
- **Settings** → **Resources** → **Advanced**
- **CPUs**: 4+ (大規模ネットワークの場合)
- **Memory**: 8GB+ (大規模ネットワークの場合)

---

## 16. よくある質問 (FAQ)

### Q1: WSL2とWSL1の違いは？

**A**: WSL2は完全なLinuxカーネルを使用し、Dockerが動作します。このプロジェクトにはWSL2が必須です。

### Q2: Windowsから直接WSLのファイルにアクセスできる？

**A**: はい。エクスプローラーで `\\wsl$\Ubuntu-22.04\home\<username>\batfish_vis` でアクセス可能です。

### Q3: VSCodeでWSL内のファイルを編集したい

**A**: VSCodeに **Remote - WSL** 拡張機能をインストールし、WSLターミナルから `code .` を実行してください。

### Q4: WSLを再起動するには？

```powershell
# Windows PowerShell
wsl --shutdown
wsl
```

### Q5: バックエンドとフロントエンドの両方をWSLで動かせる？

**A**: 可能ですが、Windows側のブラウザからアクセスしやすくするため、フロントエンドはWindows上で動かすことを推奨します。

### Q6: uvとpip/venvの違いは？

**A**: uvはRustで書かれた高速なPythonパッケージマネージャーです。主な利点:
- **速度**: pipより10-100倍高速なインストール
- **依存関係解決**: より正確で高速な依存関係解決
- **統合**: 仮想環境作成とパッケージ管理を統合

従来の方法と比較:
```bash
# 従来 (venv + pip)
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# uv使用
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Q7: uvで作成した仮想環境をpipで使える？

**A**: はい。uvで作成した `.venv` は通常のPython仮想環境なので、アクティベート後は `pip` でも操作可能です。ただし、インストール速度の利点を得るには `uv pip` の使用を推奨します。

---

## まとめ

このWSL Ubuntu環境セットアップにより:

- ✅ **Batfishコンテナ**: WSL Ubuntu上のDockerで動作 (Linux最適化)
- ✅ **バックエンドAPI**: WSL Ubuntu上のuv + Pythonで動作 (高速環境構築)
- ✅ **フロントエンド**: Windows上のNode.jsで動作 (ネイティブ開発体験)
- ✅ **シームレスな連携**: WSL2のlocalhost共有により透過的な通信

**uvの採用により**:
- 初回セットアップ時間が大幅に短縮
- 依存パッケージのインストールが10-100倍高速化
- 開発効率と実行性能を両立したハイブリッド環境が実現

開発効率と実行性能を両立したハイブリッド環境が構築できます。

**次のステップ**: 実際にネットワーク設定ファイルをアップロードしてトポロジーを表示してみましょう！
