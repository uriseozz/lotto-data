# lotto-data

로또 6/45 데이터 저장소. `lotto_insight` 앱이 이 데이터를 내려받아 사용한다.

## 당첨번호

- **`lotto.json`** — 1회차부터 최신 회차까지 전체 당첨번호/등위별 상세.
- **`update_lotto.py`** — dhlottery 신규 API를 크롤링해 새 회차를 `lotto.json`에 추가.
- **`.github/workflows/update.yml`** — 매주 토요일(추첨 후) 자동 실행되어 `lotto.json`을 갱신·커밋한다.

받는 URL: `https://raw.githubusercontent.com/uriseozz/lotto-data/main/lotto.json`

## 배출점 (1·2등 당첨점)

- **`stores.json`** — 262회차부터 최신 회차까지 1·2등 배출점 전체(상호/주소/좌표/자동수동 등).
  - 배출점 데이터는 **262회차부터** 존재한다(그 이전은 dhlottery 미공개).
- **`update_stores.py`** — dhlottery 배출점 API를 크롤링해 새 회차를 `stores.json`에 추가.
  - 과거 회차는 다시 받지 않고, 아직 미확정인 최신 회차는 다음 실행에서 자동 재시도한다.
- **`.github/workflows/update-stores.yml`** — 매주 일·화(추첨 후, 배출점 확정 지연 대비) 자동 실행.

받는 URL: `https://raw.githubusercontent.com/uriseozz/lotto-data/main/stores.json`

### stores.json 형식

```json
{
  "latest": 1231,
  "start": 262,
  "updated_at": "2026-07-10",
  "rounds_count": 970,
  "count": 78000,
  "empty": [],
  "stores": [
    {
      "round": 1231, "rank": 1,
      "shop_id": "11110385",
      "name": "복권명당ㆍ토탈클린",
      "addr": "서울 은평구 갈현로 304 1층",
      "tel": "02-353-4141",
      "method": "자동",
      "region": "서울", "gugun": "은평구",
      "lat": 37.623964, "lot": 126.91715
    }
  ]
}
```

- `rank` — 1(1등 배출점) / 2(2등 배출점)
- `shop_id` — 판매점 고유 ID. 같은 상점의 누적 당첨(명당 랭킹)은 이 값으로 집계.
- `method` — 자동 / 수동 / 반자동
- `lat`/`lot` — 위경도(지도 마커용)
- `empty` — 데이터가 끝내 없는 것으로 확정된 회차(재시도 skip 목록)

## 당첨번호 형식 (lotto.json)

```json
{
  "latest": 1231,
  "updated_at": "2026-07-04",
  "count": 1231,
  "rounds": [
    { "id": 1, "draw_date": "2002-12-07", "n1": 10, "...": "...", "bonus": 16,
      "first_prize_total": 0, "first_prize_each": 0, "first_winners": 0,
      "total_sales": 0, "second_prize_each": 0,
      "rank1_auto": 0, "rank1_manual": 0, "rank1_semi_auto": 0 }
  ]
}
```

## 수동 갱신

Actions 탭 → 워크플로 선택 → **Run workflow** 버튼.
로컬에서는 `python update_lotto.py` / `python update_stores.py` 실행.

> ⚠️ 로또 당첨번호·배출점은 공개 정보다. 이 저장소는 데이터 전용이며 앱 소스는 별도 비공개 저장소에 있다.
