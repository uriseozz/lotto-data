#!/usr/bin/env python3
"""dhlottery 배출점(1·2등 당첨점) API를 크롤링해 stores.json을 갱신한다.
당첨번호(update_lotto.py)와 동일한 구조. 외부 의존성 없음(urllib).
GitHub Actions에서 주간 실행된다.

- 배출점 데이터는 262회차부터 존재한다(그 이전은 dhlottery 미공개).
- 회차별 배출점은 과거 데이터가 바뀌지 않으므로 한 번 받은 회차는 다시 안 받는다.
- 최신 회차 배출점은 추첨 며칠 뒤 확정되므로, 아직 비어있는 회차는
  다음 실행에서 다시 시도한다(자가치유). 데이터가 끝내 없는 오래된 회차는
  `empty`에 기록해 영구 skip한다.
"""
import json, os, time, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stores.json")
META = os.path.join(HERE, "stores_meta.json")  # 앱이 14MB 받기 전 최신 회차만 싸게 확인
LOTTO = os.path.join(HERE, "lotto.json")  # 최신 회차(target) 참조용
API = ("https://www.dhlottery.co.kr/wnprchsplcsrch/selectLtWnShp.do"
       "?srchWnShpRnk=all&srchLtEpsd={}")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

START = 262          # 배출점 데이터가 시작되는 회차
SETTLED_LAG = 4      # target-회차 차이가 이 이상이면 "확정"으로 보고 빈 회차 영구 skip


def fetch(rnd):
    """회차의 배출점 리스트(dict의 list)를 반환.
    데이터 없음이면 [] (빈 리스트), 네트워크/서버 실패면 None."""
    req = urllib.request.Request(API.format(rnd), headers={
        "User-Agent": UA, "Referer": "https://www.dhlottery.co.kr/",
        "Accept": "application/json, text/javascript, */*; q=0.01"})
    for _ in range(6):  # 빈 응답(200이지만 body 없음) 대비 재시도
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read().decode("utf-8").strip()
            if not body:
                time.sleep(0.4); continue
            data = json.loads(body)
            return (data.get("data") or {}).get("list") or []
        except Exception:
            time.sleep(0.5)
    return None


def clean(s):
    if s is None:
        return None
    s = " ".join(str(s).split()).strip()
    return s or None


def to_row(rnd, it):
    """배출점 API 항목을 저장 형태로 변환. round는 쿼리 파라미터라 직접 주입."""
    return {
        "round": rnd,
        "rank": it.get("wnShpRnk"),               # 1 또는 2
        "shop_id": it.get("ltShpId"),             # 판매점 고유 ID (명당 랭킹 키)
        "name": clean(it.get("shpNm")),
        "addr": clean(it.get("shpAddr")),
        "tel": clean(it.get("shpTelno")),
        "method": clean(it.get("atmtPsvYnTxt")),  # 자동/수동/반자동
        "region": clean(it.get("tm1ShpLctnAddr")) or clean(it.get("region")),  # 시도
        "gugun": clean(it.get("tm2ShpLctnAddr")), # 구/군
        "lat": it.get("shpLat"),
        "lot": it.get("shpLot"),
    }


def get_target():
    """따라잡을 최신 회차. 같은 레포의 lotto.json latest를 신뢰.
    없으면 배출점 API를 위로 훑어 마지막 데이터 회차를 추정."""
    try:
        with open(LOTTO, encoding="utf-8") as f:
            return int(json.load(f)["latest"])
    except Exception:
        pass
    # 폴백: START부터 데이터가 끊길 때까지 훑기(느림, 거의 안 쓰임)
    rnd, last = START, START - 1
    while True:
        rows = fetch(rnd)
        if rows is None or len(rows) == 0:
            break
        last = rnd
        rnd += 1
        time.sleep(0.2)
    return last


def main():
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = {"stores": [], "empty": []}

    stores = doc.get("stores", [])
    empty = set(doc.get("empty", []))
    have = {row["round"] for row in stores}

    target = get_target()
    print(f"target(최신 회차) = {target}, 보유 회차 = {len(have)}, empty = {len(empty)}")

    added_rounds = 0
    added_rows = 0
    for rnd in range(START, target + 1):
        if rnd in have or rnd in empty:
            continue
        rows = fetch(rnd)
        if rows is None:
            print(f"round {rnd}: fetch 실패 — 다음 실행에서 재시도")
            continue
        if not rows:
            if target - rnd >= SETTLED_LAG:
                empty.add(rnd)
                print(f"round {rnd}: 데이터 없음(확정) — empty 기록")
            else:
                print(f"round {rnd}: 아직 미확정 — 다음 실행에서 재시도")
            continue
        stores.extend(to_row(rnd, it) for it in rows)
        have.add(rnd)
        added_rounds += 1
        added_rows += len(rows)
        print(f"round {rnd}: +{len(rows)}개 배출점")
        time.sleep(0.25)

    if added_rounds == 0:
        print("새 회차 없음 — stores.json 변경 없음")
        return

    stores.sort(key=lambda r: (r["round"], r["rank"] or 0, r["shop_id"] or ""))
    latest = max(have) if have else target
    doc = {
        "latest": latest,
        "start": START,
        "updated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "rounds_count": len(have),
        "count": len(stores),
        "empty": sorted(empty),
        "stores": stores,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))

    # 앱용 경량 메타(최신 회차만) — 전체 stores.json(수십 MB) 다운로드 게이트
    meta = {
        "latest": latest,
        "count": len(stores),
        "updated_at": doc["updated_at"],
        "generated_at": doc["generated_at"],
    }
    with open(META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))

    print(f"wrote stores.json: +{added_rounds}회차/{added_rows}행, "
          f"latest={latest}, 총 {len(stores)}행")


if __name__ == "__main__":
    main()
