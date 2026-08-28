# ホットフィックス辞書（β運用）

このレポジトリでは、Keynakoの共有変換・ホットフィックス辞書を管理します。Keynakoは `main` ブランチの `Dictionary/data_v1.json` を定期確認し、更新をユーザ辞書と統合します。

## ユーザの方へ
Keynakoのユーザ辞書で「この変換をKeynakoと共有」をオンにして保存すると、読み・単語・品詞・重要度がこのレポジトリへ送られます。検証に通った変換は自動で `main` の辞書へ反映されます。

## 自動反映の構成

1. KeynakoがHTTPSゲートウェイへ変換を送信します。
2. `scripts/keynako_submission_gateway.gs` がGitHubの `repository_dispatch` を発行します。
3. `.github/workflows/keynako-submission.yaml` が内容を検証し、同じ読み・単語を追加または更新して `main` へコミットします。
4. Keynakoは辞書ファイルのSHAを5分おきに確認し、変更があれば端末へ取り込みます。

### ゲートウェイの初回設定

アプリへGitHubトークンを埋め込まないため、トークンはGoogle Apps Scriptのスクリプトプロパティだけに保存します。

1. `scripts/keynako_submission_gateway.gs` をGoogle Apps Scriptへ配置します。
2. 対象レポジトリだけへアクセスできるfine-grained tokenを作り、スクリプトプロパティ `GITHUB_TOKEN` に設定します。必要なら `GITHUB_OWNER` と `GITHUB_REPOSITORY` も設定します。
3. ウェブアプリとしてデプロイし、実行ユーザを所有者、アクセスを全員に設定します。
4. デプロイURLをKeynakoレポジトリのActions変数 `KEYNAKO_DICTIONARY_SUBMISSION_URL` に設定します。

トークンはアプリ、ビルド成果物、リポジトリのいずれにも含めません。

## JSONの構造


以下は `data.json` の例と各フィールドの説明です。

```json
{
    "metadata": {
        "status": "active",
        "name": "data.json",
        "description": "A JSON file containing a list of dictionaries.",
        "version": "1.0",
        "last_update": "2025-05-04T12:00:00.00"
    },
    "data": [
        {
            "word": "azooKey",
            "ruby": "あずーきー",
            "word_weight": -15.0,
            "importance": 1,
            "lcid": 1288,
            "rcid": 1288,
            "mid": 501,
            "date": "2025-05-04",
            "author": "@ensan-hcl"
        }
    ]
}
```

### トップレベル構造

| キー | 説明 |
|------|------|
| `metadata` | ファイル自体の情報（状態、バージョン、最終更新日時など） |
| `data` | 辞書エントリの配列。各要素が 1 語彙を表します。 |

#### `metadata` オブジェクト

| フィールド | 意味 |
|-----------|------|
| `status` | 辞書ファイルの状態 (`"active"` 等) |
| `name` | ファイル名 |
| `description` | ファイル内容の説明 |
| `version` | ファイルのバージョン番号 |
| `last_update` | 最終更新日時 (ISO 8601 形式) |

#### `data` のエントリ構造

| フィールド | 意味 |
|-----------|------|
| `word` | 実際に入力・表示される語彙 |
| `ruby` | 読み仮名（ふりがな） |
| `word_weight` | 変換優先度 (値が小さいほど優先度が低い、通常-15~-5程度) |
| `importance` | Keynakoで選んだ重要度 (`1`〜`5`)。既存データでは省略できます。 |
| `lcid` / `rcid` | 左文脈 / 右文脈 ID。形態素解析エンジンが前後関係を評価する際に使用します。 |
| `mid` | 基本的に501を指定 |
| `date` | エントリ登録日 (YYYY-MM-DD 形式) |
| `author` | 登録者または変更者の識別子 |
| `categories` | 共有時に選ばれた品詞カテゴリ。既存データでは省略できます。 |

---

このように **`metadata`** にファイル全体の管理情報を、**`data`** に実際の辞書レコードを保持することで、ホットフィックス辞書の自動配信とバージョン管理を容易にしています。
