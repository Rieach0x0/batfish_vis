# Implementation Plan: Batfish Snapshot & Topology Visualization

**Branch**: `001-batfish-snapshot-topology` | **Date**: 2025-11-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-batfish-snapshot-topology/spec.md`

## Summary

ネットワーク設定ファイルフォルダを読み込み、Batfishコンテナ（v2025.07.07）と統合してスナップショットを作成し、Layer 3トポロジーをD3.jsで可視化する基盤機能。さらに、Batfish検証クエリ（到達性、ACL、ルーティング）を実行して設定の正当性を確認する機能を提供。

技術的アプローチは、Pythonバックエンド（pybatfish v2025.07.07経由）でBatfishコンテナと通信し、スナップショット作成と検証クエリを処理。フロントエンドはD3.js v7でトポロジー可視化（force-directed layout）を実装。Webアプリケーション構造で、ブラウザからアクセス可能。

## Technical Context

**Language/Version**: Python 3.11 (バックエンド), JavaScript ES2022 (フロントエンド)
**Primary Dependencies**:
- Backend: **pybatfish v2025.07.07** (2025年11月21日時点最新、Batfish統合)
- Backend: FastAPI 0.109+ (Web APIサーバー)
- Frontend: **D3.js v7** (トポロジー可視化、force-directed layout)
- Container: **Batfish v2025.07.07** (Docker `batfish/allinone:v2025.07.07`)
**Storage**: Batfish内蔵ストレージ (スナップショットデータ), ファイルシステム (設定ファイル一時保存)
**Testing**: pytest (Pythonバックエンド), Jest + Testing Library (JavaScript フロントエンド), Playwright (E2Eブラウザテスト)
**Target Platform**: Webブラウザ (Chrome 100+, Firefox 100+, Safari 15+, Edge 100+)
**Project Type**: Web application (Python backend + JavaScript/HTML/CSS frontend)
**Performance Goals**:
- 10台デバイススナップショット作成 < 2分
- 50台トポロジー可視化 < 5秒
- 検証クエリレスポンス < 10秒
**Constraints**:
- Batfishコンテナは外部起動、デフォルトポート9996で接続（憲章原則I）
- トポロジー図はBatfishクエリ結果と100%一致必須（憲章原則II）
- すべての検証はBatfishクエリ使用、カスタム検証ロジック禁止（憲章原則III）
**Scale/Scope**:
- 10〜100台デバイスのネットワーク
- マルチベンダー対応（Cisco, Juniper, Arista minimum）
- 同時ユーザー数5〜20名想定

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Batfish-First Integration

**Status**: PASS
**Verification**:
- すべてのネットワーク解析にpybatfish v2025.07.07を使用
- スナップショット作成、トポロジークエリ、検証クエリはすべてBatfish APIを経由
- カスタムパーサーは一切使用しない
- 設定ファイルはBatfishに送信し、Batfishのベンダー検出を利用

### ✅ Principle II: Topology Visualization as Contract

**Status**: PASS
**Verification**:
- D3.js可視化はBatfish `get_layer3_edges()` クエリ結果を直接消費
- ノード数、エッジ数、接続関係はBatfishデータと100%一致（SC-003）
- レイアウトアルゴリズム（force-directed等）は視覚的配置のみ、データ変換なし
- トポロジーデータの真実の情報源はBatfishのみ

### ✅ Principle III: Configuration Validation is Non-Negotiable

**Status**: PASS
**Verification**:
- FR-008: すべての検証クエリはBatfishクエリ（reachability, searchFilters, routes）を使用
- カスタム検証ロジックは実装しない
- 検証結果はBatfishから返された設定ファイル名と行番号を含む（FR-009）
- Batfishがサポートしない検証は実装しない

### ✅ Principle IV: Test-First Verification Workflow (NON-NEGOTIABLE)

**Status**: PASS (計画済み)
**Verification**: Phase 0でマルチベンダーテストフィクスチャ（Cisco、Juniper、Arista）を準備し、TDDサイクルに従って実装：
1. スナップショット作成テスト（設定ファイル → Batfish → スナップショット成功）を作成
2. トポロジー可視化テスト（スナップショット → トポロジークエリ → D3.js描画）を作成
3. 検証クエリテスト（スナップショット → reachability/ACL/routing → 結果表示）を作成
4. ユーザー承認後、テスト失敗を確認
5. 実装してテスト合格
6. リファクタリング

### ✅ Principle V: Observability & Debuggability

**Status**: PASS (計画済み)
**Verification**:
- FR-011: Batfishとの全インタラクション（スナップショット作成、クエリ実行）を構造化ログとして記録
- ログ内容: スナップショット名、タイムスタンプ、クエリタイプ、パラメータ、レスポンスサマリー、エラースタックトレース
- デバッグモード実装: ブラウザコンソールに以下を出力
  - Batfishクエリの生データ
  - D3.jsレイアウトアルゴリズムパラメータ
  - ノード/エッジ数、フィルタリング決定
  - パフォーマンスメトリクス（クエリ時間、描画時間）

### 🎯 Constitution Compliance Summary

**All gates PASSED**. This featureは憲章のすべての原則に準拠しており、Phase 0リサーチに進むことが承認されました。

## Project Structure

### Documentation (this feature)

```text
specs/001-batfish-snapshot-topology/
├── plan.md              # This file
├── research.md          # Phase 0: Batfish v2025.07.07統合、D3.js可視化パターン
├── data-model.md        # Phase 1: Snapshot、Device、Interface、Edge、VerificationResult
├── quickstart.md        # Phase 1: スナップショット作成から可視化・検証までの手順
├── contracts/           # Phase 1: REST API仕様（OpenAPI）
└── checklists/
    └── requirements.md  # 既存の品質チェックリスト
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── snapshot_api.py       # スナップショット作成・管理API
│   │   ├── topology_api.py       # トポロジークエリAPI
│   │   └── verification_api.py   # 検証クエリAPI
│   ├── services/
│   │   ├── batfish_service.py    # pybatfish統合サービス
│   │   ├── snapshot_service.py   # スナップショット管理ロジック
│   │   └── file_service.py       # 設定ファイル読み込み・一時保存
│   └── models/
│       ├── snapshot.py            # Snapshotモデル
│       ├── device.py              # Device, Interfaceモデル
│       └── verification.py        # VerificationResultモデル
└── tests/
    ├── fixtures/
    │   └── configs/               # Cisco, Juniper, Aristaテストフィクスチャ
    ├── contract/
    │   ├── test_snapshot_api.py
    │   ├── test_topology_api.py
    │   └── test_verification_api.py
    ├── integration/
    │   ├── test_batfish_integration.py
    │   └── test_snapshot_lifecycle.py
    └── unit/
        ├── test_batfish_service.py
        ├── test_snapshot_service.py
        └── test_file_service.py

frontend/
├── src/
│   ├── components/
│   │   ├── SnapshotUpload.js        # 設定ファイルフォルダ選択UI
│   │   ├── TopologyVisualization.js # D3.jsトポロジー描画
│   │   ├── VerificationPanel.js     # 検証クエリ実行・結果表示
│   │   └── SnapshotManager.js       # スナップショット一覧・切り替え
│   ├── services/
│   │   ├── snapshotService.js       # スナップショットAPI呼び出し
│   │   ├── topologyService.js       # トポロジーAPI呼び出し
│   │   └── verificationService.js   # 検証API呼び出し
│   └── utils/
│       ├── d3LayoutEngine.js        # D3.jsレイアウトアルゴリズム
│       └── topologyExporter.js      # SVG/PNG エクスポート
└── tests/
    ├── unit/
    │   ├── TopologyVisualization.test.js
    │   ├── d3LayoutEngine.test.js
    │   └── topologyExporter.test.js
    └── e2e/
        ├── snapshot_creation.spec.js
        ├── topology_visualization.spec.js
        └── verification_query.spec.js
```

**Structure Decision**: Web application構造を採用。Batfish統合と検証クエリはPythonバックエンドで処理（pybatfish v2025.07.07使用）し、D3.js v7によるトポロジー可視化とインタラクティブUIはJavaScriptフロントエンドで実装。バックエンドはFastAPIでREST APIを提供し、フロントエンドはfetch API経由で通信。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

この機能はすべての憲章原則に準拠しており、複雑性の正当化は不要です。
