# Data Model: Topology Hover Information Display

**Feature**: 002-topology-hover-info
**Date**: 2025-11-21
**Purpose**: ツールチップ表示データモデルとユーザー設定の定義

## Overview

このfeatureは3つの主要エンティティを持つ：

1. **DeviceTooltipData**: デバイスノードのツールチップ表示用データ
2. **LinkTooltipData**: リンク（エッジ）のツールチップ表示用データ
3. **TooltipDisplayPreferences**: ユーザーのツールチップ表示設定

すべてのデータはBatfishスナップショットから取得され、ユーザー設定のみがブラウザlocalStorageに永続化される。

## Entity: DeviceTooltipData

**Purpose**: トポロジー図上のデバイスノードにホバーした際に表示する情報

**Source**: Batfish `get_node_properties()` クエリ結果

### Fields

| Field Name | Type | Required | Description | Batfish Source |
|------------|------|----------|-------------|----------------|
| `hostname` | string | Yes | デバイスのホスト名 | `node.hostname` |
| `vendor` | string | Yes | ベンダー名（Cisco, Juniper, Arista等） | `node.vendor` |
| `deviceType` | string | Yes | 機器タイプ（router, switch, firewall等） | `node.deviceType` |
| `interfaceCount` | integer | Yes | アクティブインターフェース数 | `count(node.interfaces.active==true)` |
| `model` | string | No | 機器モデル名 | `node.model` |
| `osVersion` | string | No | OSバージョン | `node.configuration.osVersion` |
| `managementIp` | string | No | 管理IPアドレス | `node.configuration.managementIp` |
| `location` | string | No | 物理ロケーション（データセンター名等） | `node.configuration.location` |
| `customFields` | object | No | ユーザー定義カスタムフィールド（拡張用） | N/A (future) |

### Validation Rules

- `hostname` は1〜255文字、空文字列不可
- `vendor` は列挙型: `CISCO`, `JUNIPER`, `ARISTA`, `PALO_ALTO`, `UNKNOWN`
- `deviceType` は列挙型: `ROUTER`, `SWITCH`, `FIREWALL`, `LOAD_BALANCER`, `UNKNOWN`
- `interfaceCount` は0以上の整数
- Optional fieldsがBatfishから取得できない場合は `null` または省略

### JSON Example

```json
{
  "hostname": "core-router-1",
  "vendor": "CISCO",
  "deviceType": "ROUTER",
  "interfaceCount": 24,
  "model": "Cisco ASR 9000",
  "osVersion": "IOS XR 7.3.2",
  "managementIp": "10.0.0.1",
  "location": "DC1-Rack-A-01",
  "customFields": {}
}
```

### State Transitions

なし（読み取り専用データ）

### Relationships

- 1つの `DeviceTooltipData` は1つのBatfish Node Propertyに対応
- 1つの `DeviceTooltipData` は複数の `LinkTooltipData` と関連（source/dest device）

## Entity: LinkTooltipData

**Purpose**: トポロジー図上のリンク（エッジ）にホバーした際に表示する情報

**Source**: Batfish `get_layer3_edges()` クエリ結果

### Fields

| Field Name | Type | Required | Description | Batfish Source |
|------------|------|----------|-------------|----------------|
| `sourceDevice` | string | Yes | 接続元デバイスのホスト名 | `edge.node1.hostname` |
| `sourceInterface` | string | Yes | 接続元インターフェース名 | `edge.node1Interface` |
| `destDevice` | string | Yes | 接続先デバイスのホスト名 | `edge.node2.hostname` |
| `destInterface` | string | Yes | 接続先インターフェース名 | `edge.node2Interface` |
| `sourceIp` | string | No | 接続元IPアドレス | `edge.node1Ip` |
| `destIp` | string | No | 接続先IPアドレス | `edge.node2Ip` |
| `vlan` | integer | No | VLAN ID | `edge.vlan` |
| `linkStatus` | string | No | リンクステータス | `edge.active ? "ACTIVE" : "INACTIVE"` |
| `bandwidth` | string | No | 帯域幅（例: "10 Gbps"） | `edge.bandwidth` |
| `customFields` | object | No | ユーザー定義カスタムフィールド（拡張用） | N/A (future) |

### Validation Rules

- `sourceDevice`, `destDevice` は1〜255文字、空文字列不可
- `sourceInterface`, `destInterface` は1〜100文字、空文字列不可
- `sourceIp`, `destIp` はIPv4またはIPv6形式（省略可）
- `vlan` は1〜4094の整数（省略可）
- `linkStatus` は列挙型: `ACTIVE`, `INACTIVE`, `UNKNOWN`

### JSON Example

```json
{
  "sourceDevice": "core-router-1",
  "sourceInterface": "GigabitEthernet0/0/1",
  "destDevice": "distribution-switch-2",
  "destInterface": "TenGigabitEthernet1/0/24",
  "sourceIp": "192.168.1.1",
  "destIp": "192.168.1.2",
  "vlan": 100,
  "linkStatus": "ACTIVE",
  "bandwidth": "10 Gbps",
  "customFields": {}
}
```

### State Transitions

なし（読み取り専用データ）

### Relationships

- 1つの `LinkTooltipData` は1つのBatfish Layer 3 Edgeに対応
- 1つの `LinkTooltipData` は2つの `DeviceTooltipData` と関連（source/dest）

## Entity: TooltipDisplayPreferences

**Purpose**: ユーザーのツールチップ表示設定（表示項目、遅延時間、テーマ等）

**Storage**: Browser localStorage (key: `batfish_tooltip_prefs`)

### Fields

| Field Name | Type | Required | Description | Default Value |
|------------|------|----------|-------------|---------------|
| `version` | string | Yes | 設定スキーマバージョン | `"1.0"` |
| `device.enabled` | boolean | Yes | デバイスツールチップ表示有効/無効 | `true` |
| `device.fields` | string[] | Yes | デバイス情報の表示項目 | `["hostname", "vendor", "deviceType", "interfaceCount"]` |
| `device.customFields` | string[] | No | カスタム表示項目（将来拡張） | `[]` |
| `link.enabled` | boolean | Yes | リンクツールチップ表示有効/無効 | `true` |
| `link.fields` | string[] | Yes | リンク情報の表示項目 | `["sourceDevice", "sourceInterface", "destDevice", "destInterface"]` |
| `link.customFields` | string[] | No | カスタム表示項目（将来拡張） | `[]` |
| `display.delayMs` | integer | Yes | ツールチップ表示遅延（ミリ秒） | `300` |
| `display.maxWidth` | integer | Yes | ツールチップ最大幅（ピクセル） | `400` |
| `display.theme` | string | Yes | ツールチップテーマ | `"light"` |

### Validation Rules

- `version` は semver形式（例: "1.0", "2.1"）
- `device.fields` および `link.fields` は空配列不可（最低1項目必須）
- `device.fields` の許可値: `hostname`, `vendor`, `deviceType`, `interfaceCount`, `model`, `osVersion`, `managementIp`, `location`
- `link.fields` の許可値: `sourceDevice`, `sourceInterface`, `destDevice`, `destInterface`, `sourceIp`, `destIp`, `vlan`, `linkStatus`, `bandwidth`
- `display.delayMs` は0〜2000の整数（0=即座表示、2000=2秒遅延）
- `display.maxWidth` は200〜800の整数
- `display.theme` は列挙型: `light`, `dark`

### JSON Example (localStorage format)

```json
{
  "version": "1.0",
  "tooltipPreferences": {
    "device": {
      "enabled": true,
      "fields": ["hostname", "vendor", "deviceType", "interfaceCount", "osVersion"],
      "customFields": []
    },
    "link": {
      "enabled": true,
      "fields": ["sourceDevice", "sourceInterface", "destDevice", "destInterface", "vlan", "linkStatus"],
      "customFields": []
    },
    "display": {
      "delayMs": 300,
      "maxWidth": 400,
      "theme": "light"
    }
  }
}
```

### State Transitions

```
[Default Settings] --user customizes--> [Custom Settings]
[Custom Settings] --user saves--> [Persisted to localStorage]
[Persisted Settings] --app loads--> [Applied to UI]
[Custom Settings] --user resets--> [Default Settings]
[Persisted Settings] --version mismatch--> [Migrated to new version]
```

### Relationships

- 1つの `TooltipDisplayPreferences` は1ユーザー（ブラウザセッション）に対応
- `device.fields` および `link.fields` は `DeviceTooltipData` / `LinkTooltipData` のフィールド名を参照

## Data Flow Diagram

```
┌─────────────────────────┐
│  Batfish Container      │
│  (pybatfish)            │
└───────────┬─────────────┘
            │
            │ get_node_properties()
            │ get_layer3_edges()
            ▼
┌─────────────────────────┐
│  Backend API            │
│  (Python/Flask)         │
│  /api/topology/nodes    │
│  /api/topology/edges    │
└───────────┬─────────────┘
            │
            │ JSON Response
            ▼
┌─────────────────────────┐
│  Frontend Service       │
│  topologyService.js     │
│  ・DeviceTooltipData    │
│  ・LinkTooltipData      │
└───────────┬─────────────┘
            │
            ├──────────────────────────┐
            │                          │
            ▼                          ▼
┌─────────────────────┐    ┌─────────────────────────┐
│  D3.js Topology     │    │  localStorage           │
│  Visualization      │    │  TooltipDisplay         │
│  ・Node hover       │    │  Preferences            │
│  ・Edge hover       │    │  (永続化設定)          │
└──────────┬──────────┘    └───────────┬─────────────┘
           │                           │
           │ Event trigger             │ Load/Save
           ▼                           ▼
┌──────────────────────────────────────────────────┐
│  TooltipRenderer.js                              │
│  ・Format tooltip content                        │
│  ・Apply user preferences                        │
│  ・Calculate position                            │
│  ・Render HTML tooltip                           │
└──────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────┐
│  User sees tooltip       │
└──────────────────────────┘
```

## Schema Versioning & Migration

### Version 1.0 (Current)

初期スキーマ。デバイス/リンクツールチップの基本表示項目とlocalStorage永続化。

### Future Version 2.0 (Planned)

想定される拡張：
- `customFields` の実装（Batfishカスタムクエリ結果を表示）
- `display.position` : ツールチップ表示位置の選択（カーソル追従 vs 固定位置）
- `display.animationEnabled` : ツールチップのフェードイン/アウトアニメーション

### Migration Strategy

```javascript
function migratePreferences(oldVersion, newVersion, data) {
  if (oldVersion === "1.0" && newVersion === "2.0") {
    // Add new fields with defaults
    data.display.position = "follow-cursor";
    data.display.animationEnabled = true;
    data.version = "2.0";
  }
  return data;
}
```

## Summary

| Entity | Primary Key | Source | Storage | Mutability |
|--------|-------------|--------|---------|------------|
| DeviceTooltipData | hostname | Batfish API | In-memory (frontend) | Read-only |
| LinkTooltipData | sourceDevice+sourceInterface+destDevice+destInterface | Batfish API | In-memory (frontend) | Read-only |
| TooltipDisplayPreferences | N/A (singleton per user) | User input | localStorage | Read/Write |

すべてのデータモデルはBatfish-First Integration原則に準拠し、Batfishから取得したデータを変換せずに表示します。
