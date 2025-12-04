# クイックスタート - バックエンド起動

## ⚠️ 重要：正しいコマンドを使用してください

現在、`--reload`オプション**だけ**を使うとエラーが出ます。

## ✅ 正しい起動方法

WSL Ubuntuターミナルで以下を**コピー＆ペースト**してください：

### オプション1: リロードなし（最も安定）

```bash
cd ~/batfish_vis/backend && source .venv/bin/activate && pkill -9 -f uvicorn 2>/dev/null; find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

### オプション2: リロードあり（推奨 - ファイル変更時に自動再起動）

```bash
cd ~/batfish_vis/backend && source .venv/bin/activate && pkill -9 -f uvicorn 2>/dev/null; find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null && PYTHONPATH=$PWD uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

## ✅ 起動成功の確認

以下のメッセージが表示されればOK：

```
INFO:     Application startup complete.
```

## ❌ 間違った起動方法（使わないで！）

```bash
# これはエラーになります！
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

`PYTHONPATH=$PWD`が必要です！

## 次のステップ

1. バックエンドが起動したら、ブラウザで http://localhost:5173 を開く
2. スナップショットを作成してテスト

---

**簡単なコピペ用コマンド（リロードあり・推奨）**:

```bash
cd ~/batfish_vis/backend && source .venv/bin/activate && pkill -9 -f uvicorn 2>/dev/null; find src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null && PYTHONPATH=$PWD uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```
