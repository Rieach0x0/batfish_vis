# API Contracts: Topology Hover Information Display

**Feature**: 002-topology-hover-info
**Date**: 2025-11-21

## Overview

この機能はUI拡張であり、**新しいバックエンドAPIエンドポイントは作成しません**。

Feature 001 (Batfish Snapshot & Topology Visualization) で既に実装されている以下のAPIエンドポイントを再利用します：

- `GET /api/topology/nodes` - デバイスノード情報取得（DeviceTooltipDataの元データ）
- `GET /api/topology/edges` - リンク（エッジ）情報取得（LinkTooltipDataの元データ）

## Feature 001 API Dependencies

### GET /api/topology/nodes

**Purpose**: Batfish `get_node_properties()` クエリ結果を返す

**Response Format** (Feature 001 既存):
```json
{
  "snapshot": "snapshot-2025-11-21",
  "nodes": [
    {
      "hostname": "core-router-1",
      "vendor": "CISCO",
      "deviceType": "ROUTER",
      "interfaces": [
        {
          "name": "GigabitEthernet0/0/1",
          "active": true,
          "ipAddress": "192.168.1.1"
        }
      ],
      "model": "Cisco ASR 9000",
      "osVersion": "IOS XR 7.3.2",
      "managementIp": "10.0.0.1",
      "location": "DC1-Rack-A-01"
    }
  ]
}
```

**Feature 002 Usage**:
- `nodes[].hostname` → `DeviceTooltipData.hostname`
- `nodes[].vendor` → `DeviceTooltipData.vendor`
- `nodes[].deviceType` → `DeviceTooltipData.deviceType`
- `count(nodes[].interfaces[].active == true)` → `DeviceTooltipData.interfaceCount`
- その他オプションフィールドもマッピング

**No API Changes Required**: Feature 001のレスポンスにツールチップ表示に必要なすべてのフィールドが含まれています。

### GET /api/topology/edges

**Purpose**: Batfish `get_layer3_edges()` クエリ結果を返す

**Response Format** (Feature 001 既存):
```json
{
  "snapshot": "snapshot-2025-11-21",
  "edges": [
    {
      "node1": {
        "hostname": "core-router-1",
        "interface": "GigabitEthernet0/0/1",
        "ip": "192.168.1.1"
      },
      "node2": {
        "hostname": "distribution-switch-2",
        "interface": "TenGigabitEthernet1/0/24",
        "ip": "192.168.1.2"
      },
      "vlan": 100,
      "active": true,
      "bandwidth": "10 Gbps"
    }
  ]
}
```

**Feature 002 Usage**:
- `edges[].node1.hostname` → `LinkTooltipData.sourceDevice`
- `edges[].node1.interface` → `LinkTooltipData.sourceInterface`
- `edges[].node2.hostname` → `LinkTooltipData.destDevice`
- `edges[].node2.interface` → `LinkTooltipData.destInterface`
- `edges[].node1.ip` → `LinkTooltipData.sourceIp`
- `edges[].node2.ip` → `LinkTooltipData.destIp`
- `edges[].vlan` → `LinkTooltipData.vlan`
- `edges[].active ? "ACTIVE" : "INACTIVE"` → `LinkTooltipData.linkStatus`
- `edges[].bandwidth` → `LinkTooltipData.bandwidth`

**No API Changes Required**: Feature 001のレスポンスにツールチップ表示に必要なすべてのフィールドが含まれています。

## Frontend-Only Contracts

この機能のユニークな部分はフロントエンド実装のみです：

### TooltipPreferencesService (Frontend)

**Purpose**: ツールチップ表示設定のlocalStorage永続化

**Methods**:
```typescript
interface TooltipPreferencesService {
  save(preferences: TooltipDisplayPreferences): void;
  load(): TooltipDisplayPreferences;
  reset(): void;
  validate(preferences: TooltipDisplayPreferences): boolean;
}
```

**Storage Key**: `batfish_tooltip_prefs`

**Storage Format**: `data-model.md` の `TooltipDisplayPreferences` エンティティを参照

## No OpenAPI/GraphQL Schema

この機能は既存APIを再利用するのみで、新しいエンドポイントを作成しないため、OpenAPIスキーマやGraphQLスキーマは不要です。

## Testing Contracts

### Unit Tests

- `TooltipPreferencesService.test.js`: localStorage操作のテスト
- `TooltipRenderer.test.js`: ツールチップHTML生成のテスト
- `tooltipPositioning.test.js`: 位置計算ロジックのテスト

### Integration Tests

- `test_tooltip_batfish_integration.py`: Feature 001のAPI経由でBatfishデータ取得を検証

### E2E Tests

- `topology_hover.spec.js` (Playwright): ブラウザでのホバー操作 → ツールチップ表示を検証

## Summary

| Contract Type | Status | Location |
|---------------|--------|----------|
| Backend API | ✅ Reusing Feature 001 | `/api/topology/nodes`, `/api/topology/edges` |
| Frontend Service | 🆕 New | `TooltipPreferencesService` (localStorage only) |
| OpenAPI Schema | ❌ Not Required | N/A |
| GraphQL Schema | ❌ Not Required | N/A |

この機能は**フロントエンド専用の拡張**であり、バックエンドAPIの変更は一切不要です。
