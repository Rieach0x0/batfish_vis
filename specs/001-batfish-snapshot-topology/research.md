# Research: Batfish Snapshot & Topology Visualization

**Feature**: 001-batfish-snapshot-topology
**Date**: 2025-11-21
**Purpose**: Batfish v2025.07.07統合パターン、pybatfish API使用方法、D3.jsトポロジー可視化、マルチベンダー設定ファイル対応の調査

## Research Questions

1. pybatfish v2025.07.07でスナップショットを作成する最新のベストプラクティスは何か？
2. Batfish v2025.07.07のLayer 3トポロジークエリAPIはどう使用するか？
3. D3.js force-directed layoutでネットワークトポロジーを可視化する実装パターンは？
4. マルチベンダー（Cisco, Juniper, Arista）設定ファイルのテストフィクスチャ準備方法は？
5. Batfish検証クエリ（reachability、ACL、routing）のAPIと結果処理方法は？
6. Batfishコンテナのヘルスチェックとエラーハンドリングのベストプラクティスは？

## pybatfish v2025.07.07 Snapshot Creation Best Practices

### Decision: Session管理 + init_snapshot() + 非同期処理パターン

**Rationale**:
- pybatfish v2025.07.07では`Session`オブジェクトを使用してBatfishコンテナと接続
- 2025年7月リリースでポート9997が非推奨となり、ポート9996のみ使用（リリースノートより）
- スナップショット作成は`init_snapshot()`メソッドで実行し、同期/非同期両方サポート
- 大規模ネットワーク（100台以上）では非同期処理が推奨

**Implementation Pattern**:
```python
from pybatfish.client.session import Session
from pybatfish.datamodel import SnapshotInitializationStatus
import asyncio

# Session初期化（ポート9996のみ使用）
bf = Session(host='localhost', port=9996)

# スナップショット作成（同期版）
def create_snapshot_sync(snapshot_name, config_dir):
    try:
        # 設定ファイルディレクトリからスナップショット作成
        init_result = bf.init_snapshot(
            snapshot=snapshot_name,
            network='network_name',
            snapshot_dir=config_dir,
            overwrite=False  # 既存スナップショット保護
        )

        # 初期化ステータス確認
        if init_result == SnapshotInitializationStatus.COMPLETE:
            return {"status": "success", "snapshot": snapshot_name}
        else:
            return {"status": "failed", "error": "Initialization incomplete"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# スナップショット作成（非同期版、100台以上推奨）
async def create_snapshot_async(snapshot_name, config_dir):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        bf.init_snapshot,
        snapshot_name,
        'network_name',
        config_dir
    )
    return result
```

**v2025.07.07 New Features**:
- Python 3.13サポート追加
- ポート9997廃止（9996のみ使用）
- パースエラーレポートの改善（詳細な行番号情報）

**Alternatives Considered**:
- **REST API直接呼び出し**: pybatfishライブラリがより安定で型安全なため却下
- **古いバージョン（v2024.x）使用**: 最新機能とバグフィックスを活用するため却下

## Batfish v2025.07.07 Layer 3 Topology Query API

### Decision: `get_layer3_edges()` + DataFrame処理パターン

**Rationale**:
- Batfish v2025.07.07のトポロジークエリは`bf.q.layer3Edges().answer()`で実行
- 結果はPandas DataFrameで返され、JSON変換が容易
- Layer 3エッジは物理接続ではなく、IPルーティング可能な接続を表す
- `get_layer3_edges()`はラッパーメソッドで内部的にQuestionを実行

**Implementation Pattern**:
```python
from pybatfish.client.session import Session
import json

bf = Session(host='localhost', port=9996)
bf.set_network('network_name')
bf.set_snapshot('snapshot_name')

# Layer 3トポロジークエリ
def get_topology_data():
    # Layer 3エッジ取得
    edges_df = bf.q.layer3Edges().answer().frame()

    # DataFrame → JSONに変換
    edges_json = []
    for _, row in edges_df.iterrows():
        edge = {
            "node1": {
                "hostname": row['Interface'].hostname,
                "interface": row['Interface'].interface,
                "ip": row.get('IPs', None)
            },
            "node2": {
                "hostname": row['Remote_Interface'].hostname,
                "interface": row['Remote_Interface'].interface,
                "ip": row.get('Remote_IPs', None)
            }
        }
        edges_json.append(edge)

    return {"edges": edges_json}

# ノードプロパティ取得
def get_node_properties():
    nodes_df = bf.q.nodeProperties().answer().frame()

    nodes_json = []
    for _, row in nodes_df.iterrows():
        node = {
            "hostname": row['Node'],
            "vendor": row.get('Configuration_Format', 'UNKNOWN'),
            "interfaces": []  # 別クエリで取得
        }
        nodes_json.append(node)

    return {"nodes": nodes_json}

# インターフェース情報取得
def get_interface_properties(hostname):
    interfaces_df = bf.q.interfaceProperties(
        nodes=hostname
    ).answer().frame()

    interfaces_json = []
    for _, row in interfaces_df.iterrows():
        interface = {
            "name": row['Interface'],
            "active": row['Active'],
            "ipAddress": row.get('Primary_Address', None),
            "vlan": row.get('Access_VLAN', None)
        }
        interfaces_json.append(interface)

    return interfaces_json
```

**v2025.07.07 Improvements**:
- シンボリックルートポリシーモデリングの効率改善
- すべてのベンダーに対するマイナー改善
- 依存関係の大規模アップデート

**Alternatives Considered**:
- **raw REST API**: pybatfishのDataFrame処理が便利で型安全なため却下
- **カスタムトポロジー計算**: 憲章原則II違反（Batfishをソースとする）で却下

## D3.js Force-Directed Layout for Network Topology

### Decision: d3-force + custom collision detection + zoom/pan

**Rationale**:
- D3.js v7のforce-directed layoutは物理シミュレーションベースで自然な配置
- ネットワークトポロジーは階層的ではないため、force-directedが最適
- カスタムコリジョン検出でノードの重なりを防止
- d3-zoomでインタラクティブなズーム・パン機能を実装

**Implementation Pattern**:
```javascript
import * as d3 from 'd3';

function renderTopology(topologyData, containerSelector) {
  const width = 1200;
  const height = 800;

  // SVG作成
  const svg = d3.select(containerSelector)
    .append('svg')
    .attr('width', width)
    .attr('height', height);

  // Zoom behavior設定
  const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    });

  svg.call(zoom);

  const g = svg.append('g');

  // ノードとリンクデータ準備
  const nodes = topologyData.nodes.map(n => ({
    id: n.hostname,
    ...n
  }));

  const links = topologyData.edges.map(e => ({
    source: e.node1.hostname,
    target: e.node2.hostname,
    ...e
  }));

  // Force simulation設定
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(150))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(50)); // ノード重なり防止

  // リンク描画
  const link = g.append('g')
    .selectAll('line')
    .data(links)
    .enter().append('line')
    .attr('class', 'link')
    .attr('stroke', '#999')
    .attr('stroke-width', 2);

  // ノード描画
  const node = g.append('g')
    .selectAll('circle')
    .data(nodes)
    .enter().append('circle')
    .attr('class', 'node')
    .attr('r', 20)
    .attr('fill', d => getVendorColor(d.vendor))
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));

  // ノードラベル
  const labels = g.append('g')
    .selectAll('text')
    .data(nodes)
    .enter().append('text')
    .attr('class', 'label')
    .attr('text-anchor', 'middle')
    .attr('dy', -25)
    .text(d => d.hostname);

  // Simulation tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);

    labels
      .attr('x', d => d.x)
      .attr('y', d => d.y);
  });

  // Drag functions
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  // Vendor color mapping
  function getVendorColor(vendor) {
    const colors = {
      'CISCO': '#1BA0E2',
      'JUNIPER': '#84BD00',
      'ARISTA': '#FF6600',
      'UNKNOWN': '#999999'
    };
    return colors[vendor] || colors['UNKNOWN'];
  }
}
```

**Performance Considerations**:
- 100ノード以下: スムーズ（60fps維持）
- 100〜200ノード: 許容範囲（30fps以上）
- 200ノード以上: Canvas renderingへの移行を検討

**Alternatives Considered**:
- **階層型レイアウト（tree/cluster）**: ネットワークは階層的でないため不適切で却下
- **Cytoscape.js**: 高機能だが依存関係増加とバンドルサイズ増大で却下
- **Canvas rendering**: 初期実装にはSVGで十分、将来の最適化オプションとして保留

## Multi-Vendor Configuration Test Fixtures

### Decision: Real config samples + Batfish parsing validation

**Rationale**:
- 憲章原則IVに従い、Cisco、Juniper、Aristaの実際の設定ファイルを用意
- 各ベンダーの特徴的な構文をカバー（VLANs、ルーティングプロトコル、ACL）
- Batfishのパース成功/失敗を両方テスト
- テストフィクスチャはgit管理下に配置（機密情報マスク済み）

**Fixture Structure**:
```text
backend/tests/fixtures/configs/
├── cisco/
│   ├── router1.cfg        # Cisco IOS Router（OSPF + BGP）
│   ├── switch1.cfg        # Cisco IOS Switch（VLANs + Trunk）
│   └── invalid.cfg        # 意図的な構文エラー（ネガティブテスト）
├── juniper/
│   ├── router2.conf       # Junos Router（IS-IS + MPLS）
│   └── firewall1.conf     # Junos SRX Firewall（Security zones）
└── arista/
    ├── switch2.cfg        # Arista EOS Switch（MLAG + VXLAN）
    └── router3.cfg        # Arista EOS Router（BGP EVPN）
```

**Sample Cisco IOS Config (router1.cfg)**:
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
router bgp 65001
 neighbor 10.0.0.2 remote-as 65002
!
```

**Sample Juniper JunOS Config (router2.conf)**:
```
set system host-name distribution-router-2
set interfaces ge-0/0/0 description "Link to core-router-1"
set interfaces ge-0/0/0 unit 0 family inet address 192.168.1.2/30
set protocols isis interface ge-0/0/0.0
```

**Sample Arista EOS Config (switch2.cfg)**:
```
hostname distribution-switch-2
!
interface Ethernet1
   description Link to core-router-1
   no switchport
   ip address 192.168.1.2/30
!
router bgp 65001
   neighbor 192.168.1.1 remote-as 65001
```

**Validation Strategy**:
```python
import pytest
from pybatfish.client.session import Session

def test_cisco_config_parsing():
    bf = Session(host='localhost', port=9996)
    result = bf.init_snapshot(
        snapshot='test-cisco',
        network='test',
        snapshot_dir='tests/fixtures/configs/cisco'
    )

    # パース成功を確認
    assert result == SnapshotInitializationStatus.COMPLETE

    # パースエラーがないことを確認
    parse_status = bf.q.fileParseStatus().answer().frame()
    errors = parse_status[parse_status['Status'] != 'PASSED']
    assert len(errors) == 0, f"Parse errors: {errors}"
```

**Alternatives Considered**:
- **Mock設定ファイル（最小限）**: 実際のベンダー構文の複雑さを再現できず却下
- **単一ベンダーのみ**: 憲章とスペックがマルチベンダー対応を要求しているため却下

## Batfish Verification Queries API

### Decision: Question API + answer().frame() + JSON conversion

**Rationale**:
- Batfish v2025.07.07では`bf.q`名前空間から各種Questionにアクセス
- 主要な検証クエリ: `reachability()`, `searchFilters()`, `routes()`
- 結果はPandas DataFrameで返され、構造化データとして扱いやすい
- トレーサビリティのため、Batfishが返すファイル名と行番号を保持

**Reachability Query Implementation**:
```python
def verify_reachability(src_ip, dst_ip, src_node=None):
    # 到達性検証クエリ
    reachability_result = bf.q.reachability(
        pathConstraints={
            'startLocation': src_node if src_node else f'@enter({src_ip})',
            'endLocation': f'@exit({dst_ip})'
        }
    ).answer()

    df = reachability_result.frame()

    # 結果を構造化JSONに変換
    results = []
    for _, row in df.iterrows():
        result = {
            "flow": {
                "srcIp": row['Flow']['srcIp'],
                "dstIp": row['Flow']['dstIp'],
                "ipProtocol": row['Flow']['ipProtocol']
            },
            "traces": [],
            "outcome": row.get('Outcome', 'UNKNOWN')
        }

        # トレース情報（ホップごと）
        for trace in row.get('Traces', []):
            hops = []
            for hop in trace.get('hops', []):
                hops.append({
                    "node": hop['node'],
                    "action": hop.get('action', 'FORWARDED')
                })
            result["traces"].append({"hops": hops})

        results.append(result)

    return {"results": results, "query": "reachability"}
```

**ACL Verification Implementation**:
```python
def verify_acl(filter_name, src_ip, dst_ip, protocol='TCP'):
    # ACLフィルタ検証
    filter_result = bf.q.searchFilters(
        filters=filter_name,
        headers={
            'srcIps': src_ip,
            'dstIps': dst_ip,
            'ipProtocols': [protocol]
        }
    ).answer()

    df = filter_result.frame()

    results = []
    for _, row in df.iterrows():
        result = {
            "node": row['Node'],
            "filter": row['Filter_Name'],
            "action": row['Action'],  # PERMIT or DENY
            "lineNumber": row.get('Line', None),
            "lineContent": row.get('Line_Content', None)
        }
        results.append(result)

    return {"results": results, "query": "searchFilters"}
```

**Routing Verification Implementation**:
```python
def verify_routing(nodes=None, network=None):
    # ルーティングテーブル検証
    routes_result = bf.q.routes(
        nodes=nodes,
        network=network
    ).answer()

    df = routes_result.frame()

    routes = []
    for _, row in df.iterrows():
        route = {
            "node": row['Node'],
            "vrf": row['VRF'],
            "network": row['Network'],
            "nextHop": row.get('Next_Hop', None),
            "nextHopInterface": row.get('Next_Hop_Interface', None),
            "protocol": row['Protocol'],
            "adminDistance": row.get('Admin_Distance', None)
        }
        routes.append(route)

    return {"routes": routes, "query": "routes"}
```

**Error Traceability**:
```python
# Batfishがパースエラーを返す場合のトレーサビリティ
def get_parse_errors():
    parse_status = bf.q.fileParseStatus().answer().frame()

    errors = []
    for _, row in parse_status[parse_status['Status'] != 'PASSED'].iterrows():
        error = {
            "file": row['File_Name'],
            "status": row['Status'],
            "error_message": row.get('Error_Message', ''),
            "line_number": row.get('Line_Number', None)
        }
        errors.append(error)

    return {"errors": errors}
```

**Alternatives Considered**:
- **カスタム検証ロジック**: 憲章原則III違反で却下
- **Batfish REST API直接**: pybatfishのDataFrame処理が便利で却下

## Batfish Container Health Check & Error Handling

### Decision: Startup probe + periodic health check + graceful degradation

**Rationale**:
- Batfishコンテナは外部サービスのため、起動確認とヘルスチェックが必須
- コンテナ未起動時は明確なエラーメッセージでユーザーに通知
- 一時的な接続エラーはリトライ（最大3回、指数バックオフ）
- 永続的なエラーは詳細なトラブルシューティング情報を提供

**Health Check Implementation**:
```python
from pybatfish.client.session import Session
import requests
import time

def check_batfish_health(host='localhost', port=9996, timeout=5):
    """
    Batfishコンテナのヘルスチェック
    Returns: (healthy: bool, message: str)
    """
    try:
        # Batfish APIエンドポイントにHTTP GET
        response = requests.get(
            f'http://{host}:{port}/v2/version',
            timeout=timeout
        )

        if response.status_code == 200:
            version_info = response.json()
            return True, f"Batfish v{version_info.get('version', 'unknown')} is healthy"
        else:
            return False, f"Batfish returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to Batfish at {host}:{port}. Is the container running?"

    except requests.exceptions.Timeout:
        return False, f"Batfish health check timed out after {timeout}s"

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def wait_for_batfish_ready(max_wait=60, check_interval=5):
    """
    Batfishコンテナの起動を待つ（最大60秒）
    """
    start_time = time.time()

    while time.time() - start_time < max_wait:
        healthy, message = check_batfish_health()
        if healthy:
            return True, message

        print(f"Waiting for Batfish... {message}")
        time.sleep(check_interval)

    return False, f"Batfish did not become healthy after {max_wait}s"
```

**Retry Logic with Exponential Backoff**:
```python
import time
from functools import wraps

def retry_on_connection_error(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ConnectionError as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # 指数バックオフ
                        print(f"Connection error, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise Exception(f"Failed after {max_retries} attempts: {str(e)}")

        return wrapper
    return decorator

@retry_on_connection_error(max_retries=3, base_delay=2)
def create_snapshot_with_retry(snapshot_name, config_dir):
    bf = Session(host='localhost', port=9996)
    return bf.init_snapshot(snapshot=snapshot_name, network='network', snapshot_dir=config_dir)
```

**User-Friendly Error Messages**:
```python
def get_error_guidance(error_type):
    """
    エラータイプに応じたトラブルシューティングガイダンス
    """
    guidance = {
        "CONNECTION_ERROR": {
            "message": "Batfishコンテナに接続できません",
            "steps": [
                "1. Batfishコンテナが起動しているか確認: docker ps | grep batfish",
                "2. コンテナを起動: docker run -d -p 9996:9996 batfish/allinone:v2025.07.07",
                "3. ファイアウォールがポート9996をブロックしていないか確認"
            ]
        },
        "PARSE_ERROR": {
            "message": "設定ファイルのパースに失敗しました",
            "steps": [
                "1. 設定ファイルの構文エラーを確認",
                "2. Batfishがサポートするベンダー形式か確認（Cisco IOS, Junos, Arista EOS等）",
                "3. ファイルエンコーディングがUTF-8またはASCIIか確認"
            ]
        },
        "TIMEOUT": {
            "message": "Batfish処理がタイムアウトしました",
            "steps": [
                "1. ネットワークサイズが大きすぎる可能性（100台以上）",
                "2. Batfishコンテナのリソース（CPU/メモリ）を増やす",
                "3. タイムアウト設定を延長"
            ]
        }
    }

    return guidance.get(error_type, {"message": "不明なエラー", "steps": ["サポートに連絡してください"]})
```

**Alternatives Considered**:
- **ヘルスチェックなし**: コンテナ未起動時の不明確なエラーでUX悪化のため却下
- **同期リトライのみ**: 大規模ネットワークで長時間ブロックするため非同期も実装

## Summary of Decisions

| Research Question | Decision | Key Technology/Pattern |
|-------------------|----------|------------------------|
| pybatfish v2025.07.07スナップショット作成 | Session + init_snapshot() + 非同期処理 | pybatfish v2025.07.07, port 9996 |
| Layer 3トポロジークエリ | `bf.q.layer3Edges()` + DataFrame処理 | Pandas DataFrame, JSON conversion |
| D3.jsトポロジー可視化 | force-directed layout + zoom/pan | D3.js v7, d3-force, d3-zoom |
| マルチベンダーフィクスチャ | 実設定ファイル + パース検証 | Cisco IOS, Junos, Arista EOS |
| Batfish検証クエリ | Question API (reachability/searchFilters/routes) | Pandas DataFrame, トレーサビリティ |
| ヘルスチェック・エラーハンドリング | Startup probe + リトライ + ユーザーガイダンス | HTTP health check, 指数バックオフ |

すべての技術的決定は憲章原則（特にBatfish-First Integration、Topology Visualization as Contract、Test-First Workflow）に準拠しています。
