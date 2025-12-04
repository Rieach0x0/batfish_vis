# Quickstart: Batfish Snapshot & Topology Visualization

**Feature**: 001-batfish-snapshot-topology
**Purpose**: Batfishスナップショット作成、トポロジー可視化、設定検証の使用方法

## Prerequisites

**必要なもの:**
- Docker Desktop または Docker Engine インストール済み
- Python 3.11以上
- 対応ブラウザ: Chrome 100+, Firefox 100+, Safari 15+, Edge 100+
- ネットワーク設定ファイル（Cisco IOS、Juniper JunOS、Arista EOS等）

## Step 1: Batfishコンテナの起動

最新のBatfish v2025.07.07コンテナをDockerで起動します。

```bash
# Batfishコンテナを起動（ポート9996で公開）
docker run -d \
  --name batfish \
  -p 9996:9996 \
  batfish/allinone:v2025.07.07

# コンテナが正常に起動したか確認
docker ps | grep batfish

# ヘルスチェック（APIバージョン確認）
curl http://localhost:9996/v2/version
```

**期待される出力:**
```json
{
  "version": "v2025.07.07"
}
```

**トラブルシューティング:**
- コンテナが起動しない場合: `docker logs batfish` でログを確認
- ポート9996が使用中の場合: 別のポートにマッピング（例: `-p 9998:9996`）

## Step 2: バックエンドAPIサーバーの起動

Pythonバックエンドを起動してBatfish統合APIを提供します。

```bash
# リポジトリのクローン（初回のみ）
git clone https://github.com/your-org/batfish_vis.git
cd batfish_vis

# Python仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係のインストール
cd backend
pip install -r requirements.txt

# FastAPIサーバーの起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**期待される出力:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**ヘルスチェック:**
```bash
curl http://localhost:8000/api/health
```

**期待される出力:**
```json
{
  "status": "healthy",
  "batfishVersion": "v2025.07.07",
  "apiVersion": "1.0.0"
}
```

## Step 3: フロントエンドの起動

JavaScriptフロントエンドを起動してブラウザでアクセスします。

```bash
# 別のターミナルを開く
cd frontend

# 依存関係のインストール（初回のみ）
npm install

# 開発サーバーの起動
npm run dev
```

**期待される出力:**
```
VITE v4.5.0  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**ブラウザで開く:**
```
http://localhost:5173/
```

## Step 4: ネットワーク設定ファイルの準備

スナップショット作成に使用する設定ファイルを準備します。

**ディレクトリ構造例:**
```
my-network-configs/
├── router1.cfg      # Cisco IOS Router
├── router2.conf     # Juniper JunOS Router
├── switch1.cfg      # Cisco IOS Switch
├── switch2.cfg      # Arista EOS Switch
└── firewall1.conf   # Juniper SRX Firewall
```

**サンプル設定ファイル（Cisco IOS）:**
```
hostname core-router-1
!
interface GigabitEthernet0/0/1
 description Link to distribution-switch-2
 ip address 192.168.1.1 255.255.255.252
 no shutdown
!
router ospf 1
 network 192.168.1.0 0.0.0.3 area 0
!
```

**重要:** 機密情報（パスワード、SNMP community string等）はマスクまたは削除してください。

## Step 5: スナップショットの作成

ブラウザのUI経由またはAPI経由でスナップショットを作成します。

### UI経由の場合

1. ブラウザで `http://localhost:5173/` を開く
2. 「スナップショット作成」ボタンをクリック
3. 「フォルダ選択」で設定ファイルが格納されたフォルダを選択
4. スナップショット名を入力（例: `snapshot-2025-11-21-14-30`）
5. 「作成開始」ボタンをクリック
6. プログレスバーが表示され、完了するとスナップショット詳細が表示される

### API経由の場合（curl）

```bash
# 設定ファイルを含むディレクトリを指定
SNAPSHOT_NAME="snapshot-$(date +%Y-%m-%d-%H-%M)"

curl -X POST http://localhost:8000/api/snapshots \
  -F "snapshotName=$SNAPSHOT_NAME" \
  -F "networkName=production-network" \
  -F "configFiles=@my-network-configs/router1.cfg" \
  -F "configFiles=@my-network-configs/router2.conf" \
  -F "configFiles=@my-network-configs/switch1.cfg"
```

**期待されるレスポンス:**
```json
{
  "name": "snapshot-2025-11-21-14-30",
  "network": "production-network",
  "createdAt": "2025-11-21T14:30:15Z",
  "status": "COMPLETE",
  "configFileCount": 3,
  "deviceCount": 3,
  "batfishVersion": "v2025.07.07",
  "parseErrors": []
}
```

**パースエラーがある場合:**
```json
{
  "parseErrors": [
    {
      "fileName": "old-router.cfg",
      "errorMessage": "Unsupported vendor format",
      "lineNumber": null
    }
  ]
}
```

## Step 6: トポロジーの可視化

スナップショット作成後、ネットワークトポロジーをD3.jsで可視化します。

### UI経由の場合

1. スナップショット一覧から対象のスナップショットを選択
2. 「トポロジー表示」タブをクリック
3. D3.js force-directed layoutでトポロジー図が表示される
4. インタラクティブ操作:
   - **ズーム**: マウスホイール
   - **パン**: ドラッグ
   - **ノード移動**: ノードをドラッグ
   - **詳細表示**: ノードをクリック

### API経由の場合（ノード取得）

```bash
# デバイス一覧を取得
curl "http://localhost:8000/api/topology/nodes?snapshot=$SNAPSHOT_NAME"
```

**レスポンス例:**
```json
{
  "snapshot": "snapshot-2025-11-21-14-30",
  "nodes": [
    {
      "hostname": "core-router-1",
      "vendor": "CISCO_IOS",
      "deviceType": "ROUTER",
      "interfaces": [
        {
          "name": "GigabitEthernet0/0/1",
          "active": true,
          "ipAddress": "192.168.1.1/30"
        }
      ]
    }
  ]
}
```

### API経由の場合（エッジ取得）

```bash
# Layer 3エッジ一覧を取得
curl "http://localhost:8000/api/topology/edges?snapshot=$SNAPSHOT_NAME"
```

**レスポンス例:**
```json
{
  "snapshot": "snapshot-2025-11-21-14-30",
  "edges": [
    {
      "sourceDevice": "core-router-1",
      "sourceInterface": "GigabitEthernet0/0/1",
      "destDevice": "distribution-switch-2",
      "destInterface": "TenGigabitEthernet1/0/24",
      "sourceIp": "192.168.1.1",
      "destIp": "192.168.1.2"
    }
  ]
}
```

## Step 7: 設定検証の実行

Batfish検証クエリを実行してネットワーク設定の正当性を確認します。

### 到達性検証（Reachability）

**UI経由:**
1. 「検証」タブをクリック
2. 「到達性検証」を選択
3. 送信元IP: `10.0.1.1`
4. 宛先IP: `10.0.2.1`
5. 「実行」ボタンをクリック

**API経由:**
```bash
curl -X POST http://localhost:8000/api/verification/reachability \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot": "snapshot-2025-11-21-14-30",
    "srcIp": "10.0.1.1",
    "dstIp": "10.0.2.1"
  }'
```

**レスポンス例:**
```json
{
  "queryId": "550e8400-e29b-41d4-a716-446655440000",
  "queryType": "REACHABILITY",
  "executedAt": "2025-11-21T15:00:00Z",
  "status": "SUCCESS",
  "results": [
    {
      "flow": {
        "srcIp": "10.0.1.1",
        "dstIp": "10.0.2.1"
      },
      "traces": [
        {
          "hops": [
            {"node": "core-router-1", "action": "FORWARDED"},
            {"node": "distribution-switch-2", "action": "FORWARDED"},
            {"node": "edge-router-3", "action": "DELIVERED"}
          ]
        }
      ],
      "outcome": "SUCCESS"
    }
  ],
  "executionTimeMs": 2340
}
```

### ACL検証（searchFilters）

```bash
curl -X POST http://localhost:8000/api/verification/acl \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot": "snapshot-2025-11-21-14-30",
    "filterName": "OUTSIDE-IN",
    "srcIp": "192.0.2.100",
    "dstIp": "10.0.1.50",
    "protocol": "TCP"
  }'
```

**レスポンス例:**
```json
{
  "queryId": "660e8400-e29b-41d4-a716-446655440001",
  "queryType": "ACL_FILTER",
  "status": "SUCCESS",
  "results": [
    {
      "node": "edge-firewall-1",
      "filter": "OUTSIDE-IN",
      "action": "DENY",
      "lineNumber": 25,
      "lineContent": "deny tcp any host 10.0.1.50"
    }
  ]
}
```

### ルーティング検証（routes）

```bash
curl -X POST http://localhost:8000/api/verification/routing \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot": "snapshot-2025-11-21-14-30",
    "nodes": ["core-router-1"],
    "network": "10.0.0.0/8"
  }'
```

## Step 8: トポロジー図のエクスポート

可視化されたトポロジー図をSVGまたはPNG形式でエクスポートします。

**UI経由:**
1. トポロジー表示画面で「エクスポート」ボタンをクリック
2. 形式を選択（SVG または PNG）
3. ファイルがダウンロードされる

**ファイル名例:** `topology-snapshot-2025-11-21-14-30.svg`

## Troubleshooting

### スナップショット作成が失敗する

**症状:** `status: "FAILED"` または設定ファイルがパースされない

**解決策:**
1. 設定ファイルが正しいベンダーフォーマットか確認（Cisco IOS, Junos, Arista EOS等）
2. `parseErrors` 配列を確認し、エラーメッセージを読む
3. Batfishがサポートするベンダー一覧を確認: https://github.com/batfish/batfish/tree/master/projects/batfish/src/main/antlr4/org/batfish/grammar
4. ファイルエンコーディングがUTF-8またはASCIIか確認

### トポロジー図が表示されない

**症状:** 空白画面またはノード/エッジが0件

**解決策:**
1. スナップショットが正常に作成されたか確認（`status: "COMPLETE"`）
2. `deviceCount` が0より大きいか確認
3. ブラウザコンソール（F12）でJavaScriptエラーを確認
4. API `/topology/nodes` と `/topology/edges` を直接呼び出してデータを確認

### 検証クエリがタイムアウトする

**症状:** `status: "TIMEOUT"` または長時間応答がない

**解決策:**
1. ネットワークサイズが大きすぎる可能性（100台以上）
2. Batfishコンテナのリソース（CPU/メモリ）を増やす: `docker run --cpus=4 --memory=8g ...`
3. バックエンドAPIのタイムアウト設定を延長

### Batfishコンテナに接続できない

**症状:** `503 Service Unavailable` または `CONNECTION_ERROR`

**解決策:**
1. Batfishコンテナが起動しているか確認: `docker ps | grep batfish`
2. ポート9996がリッスンしているか確認: `netstat -an | grep 9996`
3. ファイアウォールがポート9996をブロックしていないか確認
4. バックエンドの環境変数でBatfishホスト/ポートが正しく設定されているか確認

## Next Steps

- **Feature 002 Quickstart**: トポロジーホバー情報表示機能を確認
- **data-model.md**: データモデルの詳細を確認
- **contracts/openapi.yaml**: REST API仕様の完全なドキュメントを確認
- **research.md**: 実装の技術的背景を確認

## Summary

| 操作 | コマンド/UI | 結果 |
|------|------------|------|
| Batfish起動 | `docker run batfish/allinone:v2025.07.07` | ポート9996でリッスン |
| バックエンド起動 | `uvicorn main:app` | ポート8000でREST API提供 |
| フロントエンド起動 | `npm run dev` | ポート5173でWebUI提供 |
| スナップショット作成 | UI or POST `/api/snapshots` | Batfishスナップショット生成 |
| トポロジー可視化 | UI or GET `/api/topology/nodes|edges` | D3.js force-directed layout |
| 到達性検証 | UI or POST `/api/verification/reachability` | パケットフロー検証 |
| ACL検証 | UI or POST `/api/verification/acl` | フィルタルール検証 |
| ルーティング検証 | UI or POST `/api/verification/routing` | ルーティングテーブル検証 |
