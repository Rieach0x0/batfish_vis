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
│                    フロントエンド                        │
│  (Vanilla JS + D3.js + Vite)                           │
│  - トポロジー可視化                                      │
│  - スナップショット管理UI                                │
│  - 検証パネル                                           │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼───────────────────────────────────────┐
│                   バックエンド                           │
│  (Python 3.11 + FastAPI + Pydantic V2)                 │
│  - APIエンドポイント                                     │
│  - ビジネスロジックサービス                              │
│  - エラーハンドリング＆ログ                              │
└─────────────────┬───────────────────────────────────────┘
                  │ pybatfish クライアント
┌─────────────────▼───────────────────────────────────────┐
│                 Batfish サービス                         │
│  (Docker コンテナ - v2025.07.07)                       │
│  - 設定分析                                             │
│  - トポロジー抽出                                        │
│  - 検証クエリ                                           │
└─────────────────────────────────────────────────────────┘
```

## クイックスタート

### 前提条件

- **Docker**: Batfishサービス実行用
- **Python 3.11+**: バックエンド用
- **Node.js 18+**: フロントエンド開発用

### 1. Batfishサービスの起動

```bash
docker run -d --name batfish -p 9996:9996 batfish/allinone:v2025.07.07
```

Batfishが起動していることを確認:
```bash
docker logs batfish | grep "Listening on"
```

### 2. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# バックエンドサーバーの起動
PYTHONPATH=$PWD uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

バックエンドのアクセス先: http://localhost:8000

APIドキュメント: http://localhost:8000/docs

### 3. フロントエンドのセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

フロントエンドのアクセス先: http://localhost:5173

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

### Batfish接続失敗

**症状**: バックエンドログに「Cannot connect to Batfish」と表示

**解決方法**:
```bash
# Batfishコンテナの状態確認
docker ps | grep batfish

# Batfishログの確認
docker logs batfish

# 必要に応じて再起動
docker restart batfish
```

### スナップショットアップロード時に422エラー

**症状**: ファイルアップロード時に422 Unprocessable Entityエラー

**よくある原因**:
- 複数のファイルタイプが混在（設定ファイルのみをアップロード）
- ファイル形式が不正
- 画像ファイルが誤って含まれている

**解決方法**: `.cfg`、`.conf`などのテキスト形式の設定ファイルのみをアップロードしてください。

詳細なトラブルシューティングは[QUICK_FIX.md](./QUICK_FIX.md)を参照してください。

## ドキュメント

- [クイックスタートガイド](./QUICK_START.md)
- [バックエンドセットアップ](./README_START_BACKEND.md)
- [トラブルシューティング](./QUICK_FIX.md)
- [機能仕様書](./specs/)
- [WSLセットアップガイド](./docs/WSL_Ubuntu_Setup.md)

## 技術スタック

### バックエンド
- **FastAPI** - モダンなPython Webフレームワーク
- **Pydantic V2** - 高性能データバリデーション
- **pybatfish** - Batfish Pythonクライアント（v2025.07.07）
- **uvicorn** - ASGIサーバー

### フロントエンド
- **Vanilla JavaScript ES2022** - フレームワーク不要
- **D3.js v7** - データ駆動型可視化
- **Vite** - 高速開発ビルドツール

### インフラ
- **Batfish** - ネットワーク設定分析エンジン
- **Docker** - コンテナ化

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
