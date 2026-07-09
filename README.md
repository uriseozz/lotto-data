# lotto-data

로또 6/45 당첨번호 데이터 저장소. `lotto_insight` 앱이 이 데이터를 내려받아 사용한다.

- **`lotto.json`** — 1회차부터 최신 회차까지 전체 당첨번호/등위별 상세.
- **`update_lotto.py`** — dhlottery 신규 API를 크롤링해 새 회차를 `lotto.json`에 추가.
- **`.github/workflows/update.yml`** — 매주 토요일(추첨 후) 자동 실행되어 `lotto.json`을 갱신·커밋한다.

## 앱에서 받는 URL

```
https://raw.githubusercontent.com/uriseozz/lotto-data/main/lotto.json
```

## 데이터 형식

```json
{
  "latest": 1231,
  "updated_at": "2026-07-04",
  "count": 1231,
  "rounds": [
    { "id": 1, "draw_date": "2002-12-07", "n1": 10, ..., "bonus": 16,
      "first_prize_total": ..., "first_prize_each": ..., "first_winners": ...,
      "total_sales": ..., "second_prize_each": ..., ...,
      "rank1_auto": ..., "rank1_manual": ..., "rank1_semi_auto": ... }
  ]
}
```

## 수동 갱신

Actions 탭 → "로또 당첨번호 주간 갱신" → **Run workflow** 버튼.
로컬에서는 `python update_lotto.py` 실행.

> ⚠️ 로또 당첨번호는 공개 정보다. 이 저장소는 데이터 전용이며 앱 소스는 별도 비공개 저장소에 있다.
