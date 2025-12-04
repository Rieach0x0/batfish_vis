# Data Model: Batfish Snapshot & Topology Visualization

**Feature**: 001-batfish-snapshot-topology
**Date**: 2025-11-21
**Purpose**: スナップショット、デバイス、インターフェース、エッジ、検証結果のデータモデル定義

## Overview

このfeatureは5つの主要エンティティを持つ：

1. **Snapshot（スナップショット）**: Batfishが解析したネットワーク設定の不変なコピー
2. **Device（デバイス）**: ネットワーク機器を表す論理エンティティ
3. **Interface（インターフェース）**: デバイスのネットワークインターフェース
4. **Edge（エッジ）**: デバイス間のLayer 3接続
5. **VerificationResult（検証結果）**: Batfishクエリの実行結果

すべてのデータはBatfish v2025.07.07から取得され、pybatfish APIを経由して処理されます。

## Entity: Snapshot

**Purpose**: Batfishが解析したネットワーク設定の不変なコピー

**Source**: pybatfish `init_snapshot()` + `list_snapshots()`

### Fields

| Field Name | Type | Required | Description | Batfish Source |
|------------|------|----------|-------------|----------------|
| `name` | string | Yes | スナップショット名（一意識別子） | ユーザー指定 + タイムスタンプ |
| `network` | string | Yes | ネットワーク名（Batfish内部の論理グループ） | ユーザー指定またはデフォルト |
| `createdAt` | ISO8601 datetime | Yes | スナップショット作成日時 | システム生成 |
| `status` | string | Yes | 初期化ステータス | `SnapshotInitializationStatus` |
| `configFileCount` | integer | Yes | 含まれる設定ファイル数 | `len(bf.q.fileParseStatus())` |
| `deviceCount` | integer | Yes | 検出されたデバイス数 | `len(bf.q.nodeProperties())` |
| `batfishVersion` | string | Yes | 使用されたBatfishバージョン | `bf.q.version()` または固定値 "v2025.07.07" |
| `parseErrors` | array[object] | No | パース失敗したファイル一覧 | `bf.q.fileParseStatus()` where status != PASSED |

### Validation Rules

- `name` は1〜100文字、英数字とハイフン・アンダースコアのみ
- `status` は列挙型: `COMPLETE`, `FAILED`, `IN_PROGRESS`
- `configFileCount` は1以上（設定ファイルが1つもない場合はスナップショット作成失敗）
- `deviceCount` は0以上（設定ファイルがあってもデバイスが検出されない場合あり）

### JSON Example

```json
{
  "name": "snapshot-2025-11-21-14-30",
  "network": "production-network",
  "createdAt": "2025-11-21T14:30:15Z",
  "status": "COMPLETE",
  "configFileCount": 15,
  "deviceCount": 12,
  "batfishVersion": "v2025.07.07",
  "parseErrors": [
    {
      "fileName": "old-router.cfg",
      "errorMessage": "Unsupported vendor format",
      "lineNumber": null
    }
  ]
}
```

### State Transitions

```
[User uploads configs] --init_snapshot()--> [IN_PROGRESS]
[IN_PROGRESS] --parsing complete--> [COMPLETE]
[IN_PROGRESS] --parsing failed--> [FAILED]
[COMPLETE] --user deletes--> [DELETED]
```

### Relationships

- 1つの `Snapshot` は複数の `Device` を含む（1:N）
- 1つの `Snapshot` は複数の `Edge` を含む（1:N）
- 1つの `Snapshot` に対して複数の `VerificationResult` が存在可能（1:N）

## Entity: Device

**Purpose**: ネットワーク機器を表す論理エンティティ

**Source**: pybatfish `bf.q.nodeProperties()`

### Fields

| Field Name | Type | Required | Description | Batfish Source |
|------------|------|----------|-------------|----------------|
| `hostname` | string | Yes | デバイスのホスト名（一意識別子） | `row['Node']` |
| `vendor` | string | Yes | ベンダー名 | `row['Configuration_Format']` |
| `deviceType` | string | No | 機器タイプ（推論） | `row.get('Device_Type')` または推論ロジック |
| `model` | string | No | 機器モデル名 | `row.get('Model')` |
| `osVersion` | string | No | OSバージョン | Batfish解析結果またはN/A |
| `interfaces` | array[Interface] | Yes | インターフェース一覧 | `bf.q.interfaceProperties(nodes=hostname)` |
| `location` | string | No | 物理ロケーション | 設定ファイル内のコメントから抽出可能 |

### Validation Rules

- `hostname` は1〜255文字、空文字列不可
- `vendor` は列挙型（推奨）: `CISCO_IOS`, `CISCO_NX_OS`, `JUNIPER`, `ARISTA`, `PALO_ALTO`, `UNKNOWN`
- `deviceType` は列挙型（推論）: `ROUTER`, `SWITCH`, `FIREWALL`, `LOAD_BALANCER`, `UNKNOWN`
- `interfaces` は空配列可能（インターフェースなしの論理デバイス）

### JSON Example

```json
{
  "hostname": "core-router-1",
  "vendor": "CISCO_IOS",
  "deviceType": "ROUTER",
  "model": "Cisco ASR 9000",
  "osVersion": "IOS XR 7.3.2",
  "interfaces": [
    {
      "name": "GigabitEthernet0/0/1",
      "active": true,
      "ipAddress": "192.168.1.1/30",
      "vlan": null
    }
  ],
  "location": "DC1-Rack-A-01"
}
```

### State Transitions

なし（読み取り専用、Batfishスナップショットから生成）

### Relationships

- 1つの `Device` は1つの `Snapshot` に属する（N:1）
- 1つの `Device` は複数の `Interface` を持つ（1:N）
- 1つの `Device` は複数の `Edge` の送信元または送信先となる（N:M）

## Entity: Interface

**Purpose**: デバイスのネットワークインターフェース

**Source**: pybatfish `bf.q.interfaceProperties()`

### Fields

| Field Name | Type | Required | Description | Batfish Source |
|------------|------|----------|-------------|----------------|
| `name` | string | Yes | インターフェース名 | `row['Interface']` |
| `active` | boolean | Yes | インターフェースの稼働状態 | `row['Active']` |
| `ipAddress` | string | No | IPアドレス（CIDR形式） | `row.get('Primary_Address')` |
| `vlan` | integer | No | Access VLAN ID | `row.get('Access_VLAN')` |
| `description` | string | No | インターフェース説明 | `row.get('Description')` |
| `bandwidth` | string | No | 帯域幅（例: "1 Gbps"） | `row.get('Bandwidth')` |
| `mtu` | integer | No | MTUサイズ | `row.get('MTU')` |

### Validation Rules

- `name` は1〜100文字、空文字列不可
- `active` はboolean（true/false）
- `ipAddress` はIPv4またはIPv6 CIDR形式（例: "192.168.1.1/30"）
- `vlan` は1〜4094の整数（省略可）

### JSON Example

```json
{
  "name": "GigabitEthernet0/0/1",
  "active": true,
  "ipAddress": "192.168.1.1/30",
  "vlan": null,
  "description": "Link to distribution-switch-2",
  "bandwidth": "1 Gbps",
  "mtu": 1500
}
```

### State Transitions

なし（読み取り専用）

### Relationships

- 1つの `Interface` は1つの `Device` に属する（N:1）
- 1つの `Interface` は複数の `Edge` の送信元または送信先となる（N:M）

## Entity: Edge

**Purpose**: デバイス間のLayer 3接続

**Source**: pybatfish `bf.q.layer3Edges()`

### Fields

| Field Name | Type | Required | Description | Batfish Source |
|------------|------|----------|-------------|----------------|
| `sourceDevice` | string | Yes | 接続元デバイスのホスト名 | `row['Interface'].hostname` |
| `sourceInterface` | string | Yes | 接続元インターフェース名 | `row['Interface'].interface` |
| `destDevice` | string | Yes | 接続先デバイスのホスト名 | `row['Remote_Interface'].hostname` |
| `destInterface` | string | Yes | 接続先インターフェース名 | `row['Remote_Interface'].interface` |
| `sourceIp` | string | No | 接続元IPアドレス | `row.get('IPs')` |
| `destIp` | string | No | 接続先IPアドレス | `row.get('Remote_IPs')` |

### Validation Rules

- `sourceDevice`, `destDevice` は1〜255文字、空文字列不可
- `sourceInterface`, `destInterface` は1〜100文字、空文字列不可
- `sourceIp`, `destIp` はIPv4またはIPv6形式（省略可）

### JSON Example

```json
{
  "sourceDevice": "core-router-1",
  "sourceInterface": "GigabitEthernet0/0/1",
  "destDevice": "distribution-switch-2",
  "destInterface": "TenGigabitEthernet1/0/24",
  "sourceIp": "192.168.1.1",
  "destIp": "192.168.1.2"
}
```

### State Transitions

なし（読み取り専用）

### Relationships

- 1つの `Edge` は1つの `Snapshot` に属する（N:1）
- 1つの `Edge` は2つの `Device` を接続する（N:M）
- 1つの `Edge` は2つの `Interface` を接続する（N:M）

## Entity: VerificationResult

**Purpose**: Batfishクエリの実行結果

**Source**: pybatfish `bf.q.reachability()`, `bf.q.searchFilters()`, `bf.q.routes()`

### Fields

| Field Name | Type | Required | Description | Batfish Source |
|------------|------|----------|-------------|----------------|
| `queryId` | string | Yes | クエリの一意識別子 | システム生成UUID |
| `queryType` | string | Yes | クエリタイプ | `REACHABILITY`, `ACL_FILTER`, `ROUTING` |
| `executedAt` | ISO8601 datetime | Yes | クエリ実行日時 | システム生成 |
| `parameters` | object | Yes | クエリパラメータ | ユーザー指定（srcIp, dstIp等） |
| `status` | string | Yes | クエリ実行ステータス | `SUCCESS`, `FAILED`, `TIMEOUT` |
| `results` | array[object] | No | クエリ結果詳細 | Batfish DataFrame → JSON |
| `errorMessage` | string | No | エラーメッセージ（失敗時） | 例外メッセージ |
| `executionTimeMs` | integer | Yes | 実行時間（ミリ秒） | システム計測 |

### Validation Rules

- `queryType` は列挙型: `REACHABILITY`, `ACL_FILTER`, `ROUTING`
- `status` は列挙型: `SUCCESS`, `FAILED`, `TIMEOUT`
- `executionTimeMs` は0以上の整数

### JSON Example (Reachability Query)

```json
{
  "queryId": "550e8400-e29b-41d4-a716-446655440000",
  "queryType": "REACHABILITY",
  "executedAt": "2025-11-21T15:00:00Z",
  "parameters": {
    "srcIp": "10.0.1.1",
    "dstIp": "10.0.2.1",
    "srcNode": "core-router-1"
  },
  "status": "SUCCESS",
  "results": [
    {
      "flow": {
        "srcIp": "10.0.1.1",
        "dstIp": "10.0.2.1",
        "ipProtocol": "TCP"
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
  "errorMessage": null,
  "executionTimeMs": 2340
}
```

### JSON Example (ACL Filter Query)

```json
{
  "queryId": "660e8400-e29b-41d4-a716-446655440001",
  "queryType": "ACL_FILTER",
  "executedAt": "2025-11-21T15:05:00Z",
  "parameters": {
    "filterName": "OUTSIDE-IN",
    "srcIp": "192.0.2.100",
    "dstIp": "10.0.1.50",
    "protocol": "TCP"
  },
  "status": "SUCCESS",
  "results": [
    {
      "node": "edge-firewall-1",
      "filter": "OUTSIDE-IN",
      "action": "DENY",
      "lineNumber": 25,
      "lineContent": "deny tcp any host 10.0.1.50"
    }
  ],
  "errorMessage": null,
  "executionTimeMs": 1200
}
```

### State Transitions

```
[User requests verification] --execute query--> [IN_PROGRESS]
[IN_PROGRESS] --query success--> [SUCCESS]
[IN_PROGRESS] --query failed--> [FAILED]
[IN_PROGRESS] --timeout--> [TIMEOUT]
```

### Relationships

- 1つの `VerificationResult` は1つの `Snapshot` に対して実行される（N:1）
- VerificationResultは独立したエンティティ（他エンティティへの直接参照なし）

## Data Flow Diagram

```
┌─────────────────────────┐
│  User Uploads           │
│  Config Files           │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Backend API            │
│  /api/snapshots/create  │
└───────────┬─────────────┘
            │
            │ pybatfish init_snapshot()
            ▼
┌─────────────────────────┐
│  Batfish Container      │
│  v2025.07.07            │
│  Port 9996              │
└───────────┬─────────────┘
            │
            │ Snapshot created
            ▼
┌────────────────────────────────────┐
│  Backend queries Batfish:          │
│  ・bf.q.nodeProperties()           │
│  ・bf.q.interfaceProperties()      │
│  ・bf.q.layer3Edges()              │
└────────────┬───────────────────────┘
             │
             │ DataFrames → JSON
             ▼
┌─────────────────────────┐
│  REST API Response      │
│  ・Snapshot             │
│  ・Devices              │
│  ・Interfaces           │
│  ・Edges                │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Frontend D3.js         │
│  Topology Rendering     │
└─────────────────────────┘

            ┌──────────────────────┐
            │  User Verification   │
            │  Request             │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  Backend API             │
            │  /api/verification/run   │
            └──────────┬───────────────┘
                       │
                       │ bf.q.reachability() etc.
                       ▼
            ┌──────────────────────┐
            │  Batfish Container   │
            └──────────┬───────────┘
                       │
                       │ Results
                       ▼
            ┌──────────────────────────┐
            │  VerificationResult      │
            │  Stored + Returned       │
            └──────────────────────────┘
```

## Schema Versioning

### Version 1.0 (Current)

初期スキーマ。Batfish v2025.07.07との統合、基本的なスナップショット・トポロジー・検証機能をサポート。

### Future Considerations

- **Snapshot差分機能**: 2つのスナップショットの差分を検出
- **履歴管理**: スナップショットの変更履歴を追跡
- **カスタムクエリ**: ユーザー定義のBatfishクエリをサポート

## Summary

| Entity | Primary Key | Source | Storage | Mutability |
|--------|-------------|--------|---------|------------|
| Snapshot | name | pybatfish init_snapshot | Backend DB/File | Read-only (created once) |
| Device | hostname | bf.q.nodeProperties() | In-memory (API response) | Read-only |
| Interface | hostname + name | bf.q.interfaceProperties() | In-memory (API response) | Read-only |
| Edge | sourceDevice + sourceInterface + destDevice + destInterface | bf.q.layer3Edges() | In-memory (API response) | Read-only |
| VerificationResult | queryId | bf.q.reachability/searchFilters/routes | Backend DB/File | Read-only (created once) |

すべてのデータモデルはBatfish-First Integration原則に準拠し、Batfishから取得したデータを変換せずに保存・提供します。
