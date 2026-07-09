#!/usr/bin/env python3
"""dhlottery 신규 API를 크롤링해 lotto.json에 새 회차를 추가한다.
외부 의존성 없음(urllib). GitHub Actions에서 주간 실행된다."""
import json, os, time, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "lotto.json")
API = "https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do?srchLtEpsd={}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

COLS = ["id","draw_date","n1","n2","n3","n4","n5","n6","bonus",
        "first_prize_total","first_prize_each","first_winners","total_sales",
        "second_prize_each","second_winners","third_prize_each","third_winners",
        "fourth_prize_each","fourth_winners","fifth_prize_each","fifth_winners",
        "rank1_auto","rank1_manual","rank1_semi_auto"]


def fetch(rnd):
    """회차 JSON을 받아 dict 반환. 미추첨이면 'UNDRAWN', 실패면 None."""
    req = urllib.request.Request(API.format(rnd), headers={
        "User-Agent": UA, "Referer": "https://www.dhlottery.co.kr/",
        "Accept": "application/json, text/javascript, */*; q=0.01"})
    for _ in range(15):  # 빈 응답(200이지만 body 없음)이 잦아 넉넉히 재시도
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                body = r.read().decode("utf-8").strip()
            if not body:
                time.sleep(0.4); continue
            data = json.loads(body)
            lst = (data.get("data") or {}).get("list") or []
            return "UNDRAWN" if not lst else lst[0]
        except Exception:
            time.sleep(0.4)
    return None


def ymd(s):
    s = str(s)
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else s


def to_row(it):
    return {
        "id": it["ltEpsd"], "draw_date": ymd(it["ltRflYmd"]),
        "n1": it["tm1WnNo"], "n2": it["tm2WnNo"], "n3": it["tm3WnNo"],
        "n4": it["tm4WnNo"], "n5": it["tm5WnNo"], "n6": it["tm6WnNo"],
        "bonus": it["bnsWnNo"],
        "first_prize_total": it.get("rnk1SumWnAmt"),
        "first_prize_each": it.get("rnk1WnAmt"),
        "first_winners": it.get("rnk1WnNope"),
        "total_sales": it.get("wholEpsdSumNtslAmt"),
        "second_prize_each": it.get("rnk2WnAmt"), "second_winners": it.get("rnk2WnNope"),
        "third_prize_each": it.get("rnk3WnAmt"), "third_winners": it.get("rnk3WnNope"),
        "fourth_prize_each": it.get("rnk4WnAmt"), "fourth_winners": it.get("rnk4WnNope"),
        "fifth_prize_each": it.get("rnk5WnAmt"), "fifth_winners": it.get("rnk5WnNope"),
        "rank1_auto": it.get("winType1"), "rank1_manual": it.get("winType2"),
        "rank1_semi_auto": it.get("winType3"),
    }


def main():
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = {"latest": 0, "rounds": []}

    rounds = doc.get("rounds", [])
    latest = doc.get("latest", 0)
    added = 0
    rnd = latest + 1
    while True:
        it = fetch(rnd)
        if it is None:
            print(f"round {rnd}: fetch failed — stop"); break
        if it == "UNDRAWN":
            print(f"round {rnd}: undrawn — up to date"); break
        rounds.append(to_row(it))
        latest = it["ltEpsd"]
        added += 1
        print(f"round {rnd}: added ({ymd(it['ltRflYmd'])})")
        rnd += 1
        time.sleep(0.2)

    if added == 0:
        print("no new rounds — lotto.json unchanged")
        return

    rounds.sort(key=lambda r: r["id"])
    doc = {
        "latest": latest,
        "updated_at": rounds[-1]["draw_date"],
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "count": len(rounds),
        "rounds": rounds,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote lotto.json: +{added} rounds, latest={latest}, count={len(rounds)}")


if __name__ == "__main__":
    main()
