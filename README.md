# Batfish ネットワーク可視化ツール

[Batfish](https://www.batfish.org/)を使用したネットワークトポロジー可視化および設定検証ツール

## 概要

batfish_visは、Batfishを活用してネットワークトポロジーをインタラクティブに可視化し、設定検証を行うWebインターフェースを提供します。ネットワーク機器の設定ファイルをアップロードし、トポロジーを探索し、検証クエリを実行してネットワークが意図通りに動作することを確認できます。

### 主な機能

- **スナップショット管理**: ネットワーク設定スナップショットのアップロードと管理（Cisco、Juniper、Arista対応）
- **インタラクティブなトポロジー可視化**: D3.jsによる力学モデルグラフ（ズーム、パン、ドラッグ対応）
- **機器情報表示**: ノードやリンクにマウスを当てると詳細な機器・インターフェース情報を表示
- **ネットワーク検証**: 到達性、ACL分析、ルーティング検証などのクエリ実行
- **RESTful API**: 自動化と統合のためのフル機能API

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                   Windows 環境                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │           フロントエンド (Windows)                 │ │
│  │  (Vanilla JS + D3.js + Vite)                      │ │
│  │  - トポロジー可視化                                │ │
│  │  - スナップショット管理UI                          │ │
│  │  - 検証パネル                                      │ │
│  └────────────────┬──────────────────────────────────┘ │
│                   │ HTTP/REST API (localhost:8000)     │
│  ┌────────────────▼──────────────────────────────────┐ │
│  │              WSL2 Ubuntu 環境                      │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │      バックエンド (WSL2 Ubuntu)              │ │ │
│  │  │  (Python 3.11 + FastAPI + Pydantic V2)      │ │ │
│  │  │  - APIエンドポイント                         │ │ │
│  │  │  - ビジネスロジックサービス                  │ │ │
│  │  │  - エラーハンドリング＆ログ                  │ │ │
│  │  └────────────┬─────────────────────────────────┘ │ │
│  │               │ pybatfish クライアント              │ │
│  │  ┌────────────▼─────────────────────────────────┐ │ │
│  │  │    Batfish サービス (Docker in WSL2)        │ │ │
│  │  │  (Docker コンテナ - v2025.07.07)            │ │ │
│  │  │  - 設定分析                                  │ │ │
│  │  │  - トポロジー抽出                            │ │ │
│  │  │  - 検証クエリ                                │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

※ バックエンドとBatfishはWSL2 Ubuntu上で動作
※ フロントエンドはWindows上のブラウザでアクセス
※ ファイルは /mnt/d/batfish_vis 経由でWSL2からアクセス
```

## クイックスタート

### 前提条件

#### Windows環境
- **Windows 10/11**: WSL2対応バージョン
- **Docker Desktop for Windows**: WSL2バックエンド有効
- **Node.js 18+**: フロントエンド開発用（Windows上にインストール）
- **Windows Terminal**: 推奨（複数ターミナルを並行操作）

#### WSL2環境
- **Ubuntu 22.04 LTS**: WSL2上にインストール
- **Python 3.11+**: バックエンド用
- **uv**: Python環境管理ツール（推奨）

### 0. WSL2とDocker Desktopのセットアップ

#### WSL2のインストール（未インストールの場合）

PowerShellを**管理者権限**で開き実行:
```powershell
# WSL2とUbuntuをインストール
wsl --install -d Ubuntu-22.04

# WSL2がデフォルトバージョンであることを確認
wsl --set-default-version 2
```

インストール後、Ubuntuを起動してユーザー名とパスワードを設定。

#### Docker DesktopのWSL2統合

1. Docker Desktop for Windowsを起動
2. **Settings** → **Resources** → **WSL Integration**
3. **Enable integration with my default WSL distro** をオン
4. **Ubuntu-22.04** をオン
5. **Apply & Restart**

WSL Ubuntuターミナルで動作確認:
```bash
docker --version
docker ps
```

詳細は[WSLセットアップガイド](./docs/WSL_Ubuntu_Setup.md)を参照。

### 1. Batfishサービスの起動（WSL2 Ubuntu）

WSL Ubuntuターミナルを開き:

```bash
# Batfishコンテナを起動
docker run -d --name batfish -p 9996:9996 batfish/allinone:v2025.07.07
```

Batfishが起動していることを確認:
```bash
docker logs batfish | grep "Listening on"
# 出力例: INFO: Listening on 0.0.0.0:9996
```

### 2. バックエンドのセットアップ（WSL2 Ubuntu）

**重要**: WSL2からWindowsのD:ドライブ経由でプロジェクトにアクセスします。

WSL Ubuntuターミナルで:

```bash
# Windowsのプロジェクトディレクトリに移動
cd /mnt/d/batfish_vis/backend

# Python 3.11のインストール（未インストールの場合）
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# uv（Python環境管理ツール）のインストール（推奨）
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 仮想環境の作成
python3.11 -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# .envファイルの作成
cat > .env << 'EOF'
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=INFO
EOF

# バックエンドサーバーの起動
PYTHONPATH=$PWD uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

バックエンドのアクセス先: http://localhost:8000

APIドキュメント: http://localhost:8000/docs

**ポイント**:
- WSL2とWindows間のネットワークは自動でブリッジされるため、WindowsブラウザからWSL2のlocalhost:8000にアクセス可能
- ファイル変更はWindows側（D:\batfish_vis）で行い、WSL2側（/mnt/d/batfish_vis）から実行

### 3. フロントエンドのセットアップ（Windows）

**Windows PowerShell**または**コマンドプロンプト**で:

```powershell
# プロジェクトディレクトリに移動
cd D:\batfish_vis\frontend

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

フロントエンドのアクセス先: http://localhost:5173

**ポイント**:
- フロントエンドはWindows上で動作
- WSL2で起動したバックエンド（localhost:8000）に自動接続

### 4. ネットワーク設定のアップロード

1. ブラウザで http://localhost:5173 を開く
2. 「Upload Snapshot」をクリック
3. ネットワーク設定ファイル（`.cfg`、`.conf`）を選択
4. スナップショット名を入力
5. 「Create Snapshot」をクリック

### 5. トポロジーの探索

- インタラクティブなグラフでネットワークトポロジーを可視化
- ズーム、パン、ノードのドラッグが可能
- 機器やリンクにマウスを当てると詳細情報を表示
- トポロジーをSVGまたはPNG形式でエクスポート

## 対応プラットフォーム

- Cisco IOS/IOS-XE
- Juniper Junos
- Arista EOS
- Palo Alto PAN-OS
- その他（詳細は[Batfishドキュメント](https://pybatfish.readthedocs.io/)参照）

## APIエンドポイント

### ヘルスチェック
- `GET /api/health` - サービス稼働状態の確認

### スナップショット管理
- `POST /api/snapshots` - 新規スナップショット作成
- `GET /api/snapshots` - 全スナップショット一覧
- `GET /api/snapshots/{name}` - スナップショット詳細取得
- `DELETE /api/snapshots/{name}` - スナップショット削除

### トポロジークエリ
- `GET /api/snapshots/{name}/topology/nodes` - ネットワーク機器一覧
- `GET /api/snapshots/{name}/topology/edges` - ネットワークリンク一覧
- `GET /api/snapshots/{name}/topology/interfaces` - 機器インターフェース一覧

### 検証クエリ
- `POST /api/snapshots/{name}/verification/reachability` - 到達性テスト
- `POST /api/snapshots/{name}/verification/acl` - ACL分析
- `POST /api/snapshots/{name}/verification/routing` - ルーティング検証
- `POST /api/snapshots/{name}/verification/bgp-session` - BGPセッション確認

完全なAPIドキュメント: http://localhost:8000/docs

## 開発

### バックエンド構造

```
backend/
├── src/
│   ├── api/              # REST APIエンドポイント
│   ├── services/         # ビジネスロジック
│   ├── models/           # Pydanticデータモデル
│   ├── middleware/       # エラーハンドリング、ログ
│   ├── utils/            # ユーティリティ関数
│   ├── config.py         # 設定
│   ├── exceptions.py     # カスタム例外
│   └── main.py           # FastAPIアプリケーション
├── tests/                # テストスイート（pytest）
├── requirements.txt      # Python依存関係
└── pyproject.toml        # プロジェクト設定
```

### フロントエンド構造

```
frontend/
├── src/
│   ├── components/       # UIコンポーネント
│   │   ├── SnapshotManager.js
│   │   ├── SnapshotUpload.js
│   │   ├── TopologyVisualization.js
│   │   └── VerificationPanel.js
│   ├── services/         # APIクライアントサービス
│   ├── App.js            # メインアプリケーション
│   ├── main.js           # エントリーポイント
│   └── styles.css        # スタイル
├── index.html
├── package.json          # Node依存関係
└── vite.config.js        # Vite設定
```

### テストの実行

```bash
# バックエンドテスト
cd backend
pytest

# リンティング
ruff check .
black --check .

# フロントエンドテスト（実装予定）
cd frontend
npm test
```

## 環境変数

`backend/`ディレクトリに`.env`ファイルを作成:

```env
# Batfish接続
BATFISH_HOST=localhost
BATFISH_PORT=9996

# ログ設定
LOG_LEVEL=INFO

# API設定
API_TITLE=Batfish Visualization API
API_VERSION=1.0.0
```

## トラブルシューティング

### WSL2関連

#### WSL2からDockerが使えない

**症状**: WSL2で`docker ps`を実行すると「Cannot connect to Docker daemon」エラー

**解決方法**:
1. Docker Desktop for Windowsが起動していることを確認
2. Docker Desktop → Settings → Resources → WSL Integration
3. Ubuntu-22.04の統合が有効になっていることを確認
4. WSLターミナルを再起動

```bash
# WSL再起動（Windows PowerShellで）
wsl --shutdown
# 再度WSL Ubuntuを起動
```

#### WindowsからWSL2のlocalhostにアクセスできない

**症状**: Windowsブラウザから http://localhost:8000 にアクセスできない

**解決方法**:
```bash
# WSL2でバックエンドが0.0.0.0でリッスンしていることを確認
# 127.0.0.1ではなく0.0.0.0を使用
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# WSL2のIPアドレスを確認（代替アクセス方法）
ip addr show eth0 | grep inet
```

#### ファイル変更がWSL2に反映されない

**症状**: Windows側でファイルを編集してもバックエンドに反映されない

**解決方法**:
- `/mnt/d/batfish_vis`から直接実行していることを確認
- `~/batfish_vis`にコピーした場合は同期が必要
- 推奨: `/mnt/d/batfish_vis`から直接実行（リアルタイム反映）

```bash
# 現在のディレクトリを確認
pwd
# 出力が /mnt/d/batfish_vis/backend であることを確認
```

### Batfish接続失敗

**症状**: バックエンドログに「Cannot connect to Batfish」と表示

**解決方法**（WSL2 Ubuntuで）:
```bash
# Batfishコンテナの状態確認
docker ps | grep batfish

# Batfishログの確認
docker logs batfish

# 必要に応じて再起動
docker restart batfish

# Batfishが起動しているか確認
docker logs batfish | grep "Listening on"
```

### スナップショットアップロード時に422エラー

**症状**: ファイルアップロード時に422 Unprocessable Entityエラー

**よくある原因**:
- 複数のファイルタイプが混在（設定ファイルのみをアップロード）
- ファイル形式が不正
- 画像ファイルが誤って含まれている

**解決方法**: `.cfg`、`.conf`などのテキスト形式の設定ファイルのみをアップロードしてください。

### バックエンド起動時のモジュールエラー

**症状**: `ModuleNotFoundError: No module named 'src'`

**解決方法**:
```bash
# PYTHONPATH環境変数を設定
cd /mnt/d/batfish_vis/backend
PYTHONPATH=$PWD uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

詳細なトラブルシューティングは以下を参照：
- [QUICK_FIX.md](./QUICK_FIX.md)
- [WSLセットアップガイド](./docs/WSL_Ubuntu_Setup.md)
- [同期手順](./SYNC_INSTRUCTIONS.md)

## ドキュメント

- [クイックスタートガイド](./QUICK_START.md)
- [バックエンドセットアップ](./README_START_BACKEND.md)
- [トラブルシューティング](./QUICK_FIX.md)
- [機能仕様書](./specs/)
- [WSLセットアップガイド](./docs/WSL_Ubuntu_Setup.md)

## 技術スタック

### バックエンド（WSL2 Ubuntu上で動作）
- **Python 3.11** - プログラミング言語
- **FastAPI** - モダンなPython Webフレームワーク
- **Pydantic V2** - 高性能データバリデーション
- **pybatfish** - Batfish Pythonクライアント（v2025.07.07）
- **uvicorn** - ASGIサーバー

### フロントエンド（Windows上で動作）
- **Vanilla JavaScript ES2022** - フレームワーク不要
- **D3.js v7** - データ駆動型可視化
- **Vite** - 高速開発ビルドツール
- **Node.js 18+** - JavaScriptランタイム

### インフラ
- **WSL2 (Windows Subsystem for Linux 2)** - Linux環境
- **Ubuntu 22.04 LTS** - Linuxディストリビューション
- **Docker Desktop for Windows** - コンテナ実行環境（WSL2統合）
- **Batfish v2025.07.07** - ネットワーク設定分析エンジン

## コントリビューション

コントリビューションを歓迎します！標準的なGitHubワークフローに従ってください：

1. リポジトリをフォーク
2. フィーチャーブランチを作成
3. 変更を実装
4. プルリクエストを提出

## プロジェクトステータス

**現在のバージョン**: 1.0.0（初回リリース）

**実装済み機能**:
- ✅ 機能001: Batfishスナップショット＆トポロジー可視化
- ✅ 機能002: トポロジーホバー情報表示

**ロードマップ**:
- [ ] ユニット・統合テスト
- [ ] CI/CDパイプライン（GitHub Actions）
- [ ] Docker Compose セットアップ
- [ ] スナップショットの永続化ストレージ
- [ ] ユーザー認証
- [ ] 高度な検証クエリ
- [ ] トポロジー比較（差分表示）

## ライセンス

[未定]

## 謝辞

- [Batfish](https://www.batfish.org/) - ネットワーク設定分析
- [D3.js](https://d3js.org/) - データ可視化
- [FastAPI](https://fastapi.tiangolo.com/) - モダンなPython Webフレームワーク

## サポート

問題や質問がある場合：
- GitHubでissueを作成
- `docs/`ディレクトリ内のドキュメントを確認
- トラブルシューティングガイドを参照

---

**Batfishで構築** | ネットワーク設定検証を簡単に
