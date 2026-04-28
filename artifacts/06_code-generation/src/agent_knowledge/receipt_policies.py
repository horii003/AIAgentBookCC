"""経費申請に関するバリデーションルール・申請ポリシー定数"""

DEADLINE_MONTHS: int = 3
"""申請期限: 経費発生日から何ヶ月以内に申請する必要があるか"""

MANAGER_APPROVAL_THRESHOLD: int = 5000
"""上長承認が必要な経費合計（円）"""

EXPENSE_CATEGORIES: list[str] = ["事務用品費", "宿泊費", "資格精算費", "その他経費"]
"""申請可能な経費区分"""

RETURN_RISK_KEYWORDS: list[str] = [
    "交際費",
    "飲食",
]
"""差し戻しリスクが高い経費キーワード（BRL-08）"""
