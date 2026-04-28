"""交通費申請に関するバリデーションルール・申請ポリシー定数"""

DEADLINE_MONTHS: int = 3
"""申請期限: 移動日から何ヶ月以内に申請する必要があるか"""

MANAGER_APPROVAL_THRESHOLD: int = 10000
"""上長承認が必要な交通費合計（円）"""

ALLOWED_TRANSPORT_TYPES: list[str] = ["電車", "バス", "タクシー", "飛行機"]
"""申請可能な交通手段"""

RETURN_RISK_KEYWORDS: list[str] = [
    "タクシー",
    "飛行機",
]
"""差し戻しリスクが高い交通手段キーワード（BRL-08）"""
