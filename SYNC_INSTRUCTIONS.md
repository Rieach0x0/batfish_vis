# バックエンドの変更をWSLに同期する手順

## 問題

D:\batfish_visで変更したファイルがWSL Ubuntu（~/batfish_vis）に同期されていないため、バックエンドの変更が反映されていません。

## 解決方法

### オプション1: WSLのマウントパスから直接実行（推奨）

WSL UbuntuからWindowsのD:ドライブに直接アクセスできます。

#### ステップ1: バックエンドを停止

WSL Ubuntuターミナルで:
```bash
# Ctrl+C でバックエンドを停止
```

#### ステップ2: Windowsのパスから直接実行

```bash
# Windowsのパスに移動
cd /mnt/d/batfish_vis/backend

# Python仮想環境を確認
ls -la .venv

# .venvがない場合は作成
if [ ! -d ".venv" ]; then
    uv venv --python python3.11
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# .envファイルを作成
cat > .env << 'EOF'
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=DEBUG
EOF

# バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

これにより、D:\batfish_vis\backend の最新コードが直接実行されます。

### オプション2: ファイルをWSLにコピー

#### ステップ1: バックエンドの変更ファイルをコピー

WSL Ubuntuターミナルで:

```bash
# バックエンドを停止（Ctrl+C）

# main.pyをコピー
cp /mnt/d/batfish_vis/backend/src/main.py ~/batfish_vis/backend/src/main.py

# 所有権を変更
sudo chown $USER:$USER ~/batfish_vis/backend/src/main.py

# ファイルが更新されたか確認
ls -la ~/batfish_vis/backend/src/main.py
cat ~/batfish_vis/backend/src/main.py | grep RequestValidationError
```

最後のコマンドで`RequestValidationError`が含まれていることを確認してください。

#### ステップ2: バックエンドを再起動

```bash
cd ~/batfish_vis/backend
source .venv/bin/activate

# .envファイルを作成
cat > .env << 'EOF'
BATFISH_HOST=localhost
BATFISH_PORT=9996
LOG_LEVEL=DEBUG
EOF

# バックエンドを起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

## フロントエンドの変更も同様に

フロントエンドはWindowsで直接実行しているため、変更は自動的に反映されるはずですが、正規表現の警告がまだ出ているということは、ブラウザキャッシュの問題です。

### Windows PowerShellで:

```powershell
# フロントエンドを停止（Ctrl+C）

cd D:\batfish_vis\frontend

# キャッシュを完全削除
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .vite -ErrorAction SilentlyContinue

# 再起動
npm run dev
```

### ブラウザで:

1. **すべてのタブを閉じる**
2. ブラウザを完全に終了
3. ブラウザを再起動
4. **Ctrl+Shift+Delete** でキャッシュクリア
5. http://localhost:5173 にアクセス

## 確認方法

### バックエンドの変更が反映されているか確認

WSL Ubuntuターミナルで、バックエンド起動時に以下のようなログが出力されるか確認:

```bash
INFO:     Application startup complete.
```

その後、テストリクエストを送信すると:

```
ERROR: Request validation error (422)
  url: http://localhost:8000/api/snapshots
  method: POST
  errors: [...]
ERROR: Validation error detail
  loc: ...
  msg: ...
```

このようなログが出力されれば、変更が反映されています。

### フロントエンドの変更が反映されているか確認

ブラウザで F12 → Console を開き、正規表現の警告が**出なくなっているか**確認:

```
Pattern attribute value [a-zA-Z0-9_-]+ is not a valid regular expression
```

この警告が出なくなっていれば、変更が反映されています。

## 推奨: オプション1（WSLマウントパスから直接実行）

最もシンプルで、ファイル同期の問題を回避できます。
