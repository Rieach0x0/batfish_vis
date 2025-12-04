# Implementation Plan: Topology Hover Information Display

**Branch**: `002-topology-hover-info` | **Date**: 2025-11-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-topology-hover-info/spec.md`

## Summary

トポロジー可視化機能（Feature 001）の拡張として、D3.jsで描画されたネットワークトポロジー図上のデバイスノードおよびリンク（エッジ）に対するマウスホバーイベントを検知し、Batfishから取得した情報をツールチップとして表示する。ユーザーはデバイス詳細画面に遷移せずに主要情報を素早く確認でき、さらにツールチップ表示項目をカスタマイズ可能。

技術的アプローチは、D3.jsのイベントリスナーを活用し、SVG要素（ノード/エッジ）へのマウスオーバーでBatfishデータを参照してHTMLツールチップを動的生成。表示遅延とポジション調整により最適なUXを提供。設定はブラウザのlocalStorageに永続化。

## Technical Context

**Language/Version**: Python 3.11 (バックエンド), JavaScript ES2022 (フロントエンド)
**Primary Dependencies**:
- Backend: pybatfish (Batfish統合), Flask または FastAPI (Web APIサーバー)
- Frontend: D3.js v7 (トポロジー可視化), d3-selection, d3-force (指定済み)
**Storage**: Browser localStorage (ツールチップ設定永続化), Batfish内蔵ストレージ (スナップショットデータ)
**Testing**: pytest (Pythonバックエンド), Jest + Testing Library (JavaScript フロントエンド), Playwright (E2Eブラウザテスト)
**Target Platform**: 現代的なWebブラウザ (Chrome 100+, Firefox 100+, Safari 15+, Edge 100+)
**Project Type**: Web application (Python backend + JavaScript/HTML/CSS frontend)
**Performance Goals**:
- ツールチップ表示レスポンス < 500ms
- 50台デバイストポロジーで60fps維持
- ホバーイベント処理 < 100ms
**Constraints**:
- 0.5秒以内のツールチップ表示（仕様要件）
- 画面端での自動ポジション調整必須
- Batfishコンテナとの通信はpybatfishのみ使用（憲章原則I）
**Scale/Scope**:
- 50〜100台デバイスのトポロジー図
- ツールチップ表示項目10〜15種類
- 同時ユーザー数10〜50名想定

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Batfish-First Integration
**Status**: PASS
**Verification**: ツールチップに表示するデバイス/リンク情報はすべてBatfishスナップショットから取得。Feature 001のBatfish統合基盤（pybatfish経由のトポロジークエリ）を再利用し、カスタムパーサーは使用しない。

### ✅ Principle II: Topology Visualization as Contract
**Status**: PASS
**Verification**: ツールチップはD3.jsで描画されたトポロジー図のノード/エッジデータに直接紐付き、表示される情報はBatfishの `get_layer3_edges()` および `get_node_properties()` クエリ結果と100%一致する。可視化データの変換は行わず、表示フォーマットのみ調整。

### ✅ Principle III: Configuration Validation is Non-Negotiable
**Status**: PASS (N/A)
**Verification**: この機能は設定検証ではなくUI拡張であるため、Batfish検証クエリは実行しない。表示する情報はすべてBatfishが既に解析済みのスナップショットデータから取得。

### ✅ Principle IV: Test-First Verification Workflow (NON-NEGOTIABLE)
**Status**: PASS (計画済み)
**Verification**: Phase 0でマルチベンダーテストフィクスチャ（Cisco、Juniper、Arista）を準備し、TDDサイクルに従って実装：
1. ツールチップ表示テスト（ホバーイベント → ツールチップ表示 → 正しい情報表示）を作成
2. ユーザー承認後、テスト失敗を確認
3. 実装してテスト合格
4. リファクタリング

### ✅ Principle V: Observability & Debuggability
**Status**: PASS (計画済み)
**Verification**:
- Batfish APIリクエスト（トポロジーデータ取得）のログ記録（スナップショット名、クエリタイプ、レスポンスサマリー）
- デバッグモード実装：ブラウザコンソールに以下を出力
  - ホバーイベント詳細（対象ノード/エッジID、Batfishデータ）
  - ツールチップポジション計算パラメータ
  - パフォーマンスメトリクス（イベント処理時間、描画時間）

### 🎯 Constitution Compliance Summary
**All gates PASSED**. This feature は憲章のすべての原則に準拠しており、Phase 0リサーチに進むことが承認されました。

## Project Structure

### Documentation (this feature)

```text
specs/002-topology-hover-info/
├── plan.md              # This file
├── research.md          # Phase 0: D3.jsツールチップパターン、パフォーマンス最適化
├── data-model.md        # Phase 1: TooltipData、DisplayPreferences
├── quickstart.md        # Phase 1: ツールチップ機能の使用方法
├── contracts/           # Phase 1: (このfeatureはUI拡張のためAPI contract不要)
└── checklists/
    └── requirements.md  # 既存の品質チェックリスト
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── topology_api.py      # トポロジーデータ提供API（Feature 001拡張）
│   ├── services/
│   │   └── batfish_service.py   # Batfish統合サービス（Feature 001既存）
│   └── models/
│       └── tooltip_preferences.py # ツールチップ設定モデル
└── tests/
    ├── contract/
    │   └── test_topology_api_tooltip.py
    ├── integration/
    │   └── test_tooltip_batfish_integration.py
    └── unit/
        └── test_tooltip_preferences.py

frontend/
├── src/
│   ├── components/
│   │   ├── TopologyVisualization.js   # D3.jsトポロジー描画（Feature 001既存）
│   │   ├── TooltipRenderer.js         # ツールチップ描画コンポーネント
│   │   └── TooltipSettings.js         # ツールチップ設定UI
│   ├── services/
│   │   ├── topologyService.js         # トポロジーデータ取得（Feature 001既存）
│   │   └── tooltipPreferencesService.js # 設定永続化サービス
│   └── utils/
│       ├── tooltipPositioning.js      # ツールチップ位置調整ユーティリティ
│       └── hoverDebounce.js           # ホバー遅延制御
└── tests/
    ├── unit/
    │   ├── TooltipRenderer.test.js
    │   ├── tooltipPositioning.test.js
    │   └── hoverDebounce.test.js
    └── e2e/
        └── topology_hover.spec.js     # Playwright E2Eテスト
```

**Structure Decision**: Web application構造を採用。Batfish統合はPythonバックエンドで処理し、D3.js可視化とツールチップUIはJavaScriptフロントエンドで実装。Feature 001で構築された既存のトポロジー描画基盤を拡張する形で、イベントリスナーとツールチップコンポーネントを追加。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

この機能はすべての憲章原則に準拠しており、複雑性の正当化は不要です。
