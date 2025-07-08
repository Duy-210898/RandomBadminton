import random
from flask import render_template, request, redirect, url_for, session, Blueprint
from . import db
from .models import Tournament, Group, Team, Match
from datetime import datetime

main = Blueprint("main", __name__)

# ====================================
# BƯỚC 1: NHẬP DANH SÁCH & LƯU TÊN GIẢI
# ====================================
@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        tournament_name = request.form.get("tournament_name", "").strip()
        raw_tier1 = request.form.get("tier1", "")
        raw_tier2 = request.form.get("tier2", "")
        raw_fixed = request.form.get("fixed_teams", "")

        # Tách các dòng và loại bỏ khoảng trắng
        tier1 = [x.strip() for x in raw_tier1.split("\n") if x.strip()]
        tier2 = [x.strip() for x in raw_tier2.split("\n") if x.strip()]

        # Tách các cặp cố định: mỗi dòng là "A - B"
        fixed_pairs = []
        for line in raw_fixed.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "-" not in line:
                return render_template("index.html", error="Dòng cố định không hợp lệ (thiếu dấu '-').")
            left, right = line.split("-", 1)
            fixed_pairs.append((left.strip(), right.strip()))

        # Đảm bảo tier1 và tier2 có cùng số lượng (sau khi loại bỏ các cặp cố định)
        num_t1 = len(tier1)
        num_t2 = len(tier2)
        if num_t1 != num_t2:
            tournaments = Tournament.query.order_by(Tournament.id.desc()).all()
            return render_template("index.html", error="Tier 1 và Tier 2 phải cùng số lượng.", tournaments=tournaments)

        # Shuffle danh sách còn lại
        random.shuffle(tier1)
        random.shuffle(tier2)
        paired = list(zip(tier1, tier2))

        # Gộp cặp cố định lên trước, sau đó đến các cặp random
        all_teams = fixed_pairs + paired

        # Lưu vào session
        session["teams"] = all_teams
        session["tournament_name"] = tournament_name or datetime.now().strftime("Tournament %d/%m/%Y")

        return redirect(url_for("main.show_teams"))

    # GET: Hiển thị danh sách các giải đã tạo
    tournaments = Tournament.query.order_by(Tournament.name).all()
    tournament_list = []
    for t in tournaments:
        knockout_matches = Match.query.filter_by(tournament_id=t.id, group_id=None).all()
        status = "Complete" if knockout_matches and all(m.score1 is not None and m.score2 is not None for m in knockout_matches) else "In Progress"
        tournament_list.append({
            "id": t.id,
            "name": t.name,
            "status": status,
            "status_color": "green" if status == "Complete" else "orange"
        })

    return render_template("index.html", tournaments=tournament_list)

# ====================================
# BƯỚC 2: HIỂN THỊ DANH SÁCH GHÉP ĐỘI
# ====================================
@main.route("/show_teams")
def show_teams():
    teams = session.get("teams", [])
    return render_template("show_teams.html", teams=teams)


@main.route("/assign_groups", methods=["POST"])
def assign_groups():
    from .models import Tournament, Group, Team, Match

    tournament_name = session.get("tournament_name", "").strip()
    if not tournament_name:
        tournament_name = datetime.now().strftime("Tournament %d/%m/%Y")

    num_groups = int(request.form.get("num_groups", 0))
    original_teams = list(session.get("teams", []))
    if num_groups <= 0 or not original_teams:
        return "❌ Dữ liệu không hợp lệ.", 400

    # ✅ Shuffle đội
    random.shuffle(original_teams)

    # ✅ Tạo giải đấu
    tournament = Tournament(name=tournament_name)
    db.session.add(tournament)
    db.session.commit()

    # ✅ Tạo bảng A, B, C,...
    group_objs = []
    for i in range(num_groups):
        group = Group(name=f"Group {chr(65 + i)}", tournament=tournament)
        db.session.add(group)
        group_objs.append(group)
    db.session.commit()

    # ✅ Gán đội theo bảng và gom theo group.name (không dùng id sớm)
    teams_by_group = {group.name: [] for group in group_objs}

    for idx, (tier1, tier2) in enumerate(original_teams):
        group = group_objs[idx % num_groups]
        team = Team(
            tier1=tier1,
            tier2=tier2,
            name=f"{tier1} – {tier2}",
            group=group
        )
        db.session.add(team)
        teams_by_group[group.name].append(team)

    db.session.commit()  # Lúc này team.group_id sẽ chính xác 100%
    # ✅ In danh sách đội theo bảng ra console
    for group_name, team_list in teams_by_group.items():
        print(f"\n📌 {group_name}:")
        for t in team_list:
            print(f"   - {t.name}")
    # ✅ Hàm sinh lịch vòng tròn
    def round_robin(teams):
        if len(teams) < 2:
            return []

        if len(teams) % 2 != 0:
            teams.append(None)  # BYE

        n = len(teams)
        rounds = []
        for _ in range(n - 1):
            for i in range(n // 2):
                t1, t2 = teams[i], teams[n - 1 - i]
                if t1 and t2:
                    rounds.append((t1, t2))
            # Xoay
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        return rounds

    # ✅ Tạo trận đấu cho từng bảng
    for group in group_objs:
        team_list = teams_by_group[group.name]
        matches = round_robin(team_list)
        for team1, team2 in matches:
            match = Match(
                group=group,
                tournament=tournament,
                team1=team1.name,
                team2=team2.name,
                score1=None,
                score2=None
            )
            db.session.add(match)
    db.session.commit()

    # ✅ Render kết quả
    result_groups = {
        g.name: [(t.tier1, t.tier2) for t in Team.query.filter_by(group_id=g.id).order_by(Team.id).all()]
        for g in group_objs
    }

    schedule = {
        g.name: [(m.team1, m.team2) for m in Match.query.filter_by(group_id=g.id).order_by(Match.id).all()]
        for g in group_objs
    }

    return render_template(
        "group_result.html",
        groups=result_groups,
        schedule=schedule,
        tournament=tournament
    )

# ====================================
# HIỂN THỊ DANH SÁCH CÁC GIẢI ĐẤU
# ====================================
@main.route("/tournaments")
def list_tournaments():
    tournaments = Tournament.query.order_by(Tournament.id.desc()).all()
    result = []

    for t in tournaments:
        knockout_matches = Match.query.filter_by(tournament_id=t.id, group_id=None).all()
        if knockout_matches and all(m.score1 is not None and m.score2 is not None for m in knockout_matches):
            status = "Complete"
        else:
            status = "In Progress"

        result.append({
            "id": t.id,
            "name": t.name,
            "status": status,
            "status_color": "green" if status == "Complete" else "orange"
        })

    return render_template("tournaments.html", tournaments=result)

def calculate_detailed_standings(group):
    teams = {t.name: {
        "name": t.name,
        "match_points": [],  # điểm từng trận
        "total_points": 0,
        "gd": 0
    } for t in group.teams}

    # Tạo danh sách trận liên quan từng đội để đúng thứ tự
    matches = group.matches

    for match in matches:
        if match.score1 is not None and match.score2 is not None:
            team1 = teams[match.team1]
            team2 = teams[match.team2]

            # Xử lý điểm và hiệu số đội 1
            if match.score1 > match.score2:
                team1["match_points"].append(1)
                team2["match_points"].append(0)
            elif match.score1 < match.score2:
                team1["match_points"].append(0)
                team2["match_points"].append(1)
            else:
                team1["match_points"].append(0)
                team2["match_points"].append(0)

            team1["total_points"] += team1["match_points"][-1]
            team2["total_points"] += team2["match_points"][-1]

            team1["gd"] += match.score1 - match.score2
            team2["gd"] += match.score2 - match.score1

    # Đảm bảo độ dài danh sách điểm bằng số trận mỗi đội
    num_matches_per_team = len(group.teams) - 1
    for team in teams.values():
        while len(team["match_points"]) < num_matches_per_team:
            team["match_points"].append("")

    return sorted(teams.values(), key=lambda x: (-x["total_points"], -x["gd"]))

@main.route("/tournament/<int:tournament_id>", methods=["GET", "POST"])
def view_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    groups = tournament.groups

    # Cập nhật điểm nếu POST
    if request.method == "POST":
        for match in Match.query.filter(Match.group_id.in_([g.id for g in groups])).all():
            score1 = request.form.get(f"score1_{match.id}")
            score2 = request.form.get(f"score2_{match.id}")
            if score1 is not None and score2 is not None and score1.isdigit() and score2.isdigit():
                match.score1 = int(score1)
                match.score2 = int(score2)
        db.session.commit()

    standings = {}
    for group in groups:
        standings[group.name] = calculate_detailed_standings(group)

    max_matches = max(len(group.teams) - 1 for group in groups)

    return render_template("tournament_detail.html", tournament=tournament, standings=standings, max_matches=max_matches)

@main.route("/tournament/<int:tournament_id>/generate_knockout", methods=["POST"])
def generate_knockout(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)

    existing_matches = Match.query.filter_by(tournament_id=tournament_id, group_id=None).count()
    if existing_matches >= 3:  # đủ số trận tối thiểu
        return redirect(url_for("main.view_knockout_bracket", tournament_id=tournament_id))

    # Lấy standings từng bảng
    standings = {}
    for group in tournament.groups:
        standings[group.name] = calculate_detailed_standings(group)

    group_names = sorted(standings.keys())
    if len(group_names) < 2:
        return "❌ Cần ít nhất 2 bảng", 400

    A, B = group_names[0], group_names[1]
    total_teams = sum(len(v) for v in standings.values())

    def add_match(t1, t2):
        m = Match(team1=t1, team2=t2, tournament=tournament)
        db.session.add(m)
        return m

    if total_teams == 6:
        # ✅ Trường hợp 6 đội: 3 trận
        final = add_match(standings[A][0]['name'], standings[B][0]['name'])   # Nhất A vs Nhất B
        third = add_match(standings[A][1]['name'], standings[B][1]['name'])   # Nhì A vs Nhì B
        fifth = add_match(standings[A][2]['name'], standings[B][2]['name'])   # Ba A vs Ba B
    elif total_teams == 8:
        # ✅ Trường hợp 8 đội: chuẩn 8 trận knock-out
        upper_pairs = [
            (standings[A][0]['name'], standings[B][1]['name']),
            (standings[B][0]['name'], standings[A][1]['name']),
        ]
        lower_pairs = [
            (standings[A][2]['name'], standings[B][3]['name']),
            (standings[B][2]['name'], standings[A][3]['name']),
        ]

        upper = [add_match(t1, t2) for t1, t2 in upper_pairs]
        lower = [add_match(t1, t2) for t1, t2 in lower_pairs]

        final = add_match("Winner Upper 1", "Winner Upper 2")
        third = add_match("Loser Upper 1", "Loser Upper 2")
        fifth = add_match("Winner Lower 1", "Winner Lower 2")
        seventh = add_match("Loser Lower 1", "Loser Lower 2")

    else:
        return "❌ Hiện chỉ hỗ trợ knock-out cho giải 6 hoặc 8 đội.", 400

    db.session.commit()
    return redirect(url_for("main.view_knockout_bracket", tournament_id=tournament_id))

def get_final_ranking(tournament_id):
    matches = Match.query.filter_by(tournament_id=tournament_id, group_id=None).order_by(Match.id).all()

    if len(matches) < 8:
        return []

    upper = matches[:2]
    lower = matches[2:4]
    final, third, fifth, seventh = matches[4:8]

    def winner(m):
        return m.team1 if m.score1 > m.score2 else m.team2 if m.score1 != m.score2 else m.team1

    def loser(m):
        return m.team2 if m.score1 > m.score2 else m.team1 if m.score1 != m.score2 else m.team2

    ranking = []

    # 1–2
    if final.score1 is not None and final.score2 is not None:
        ranking.append({"rank": 1, "name": winner(final)})
        ranking.append({"rank": 2, "name": loser(final)})

    # 3–4
    if third.score1 is not None and third.score2 is not None:
        ranking.append({"rank": 3, "name": winner(third)})
        ranking.append({"rank": 4, "name": loser(third)})

    # 5–6
    if fifth.score1 is not None and fifth.score2 is not None:
        ranking.append({"rank": 5, "name": winner(fifth)})
        ranking.append({"rank": 6, "name": loser(fifth)})

    # 7–8
    if seventh.score1 is not None and seventh.score2 is not None:
        ranking.append({"rank": 7, "name": winner(seventh)})
        ranking.append({"rank": 8, "name": loser(seventh)})

    return sorted(ranking, key=lambda x: x["rank"])

from flask import request

@main.route("/clear_db")
def clear_database():
    # ✅ Xác thực đơn giản qua query param
    token = request.args.get("token")
    if token != "210898":  # Đổi thành token bạn chọn
        return "❌ Không có quyền.", 403

    try:
        from .models import Match, Team, Group, Tournament

        # Xóa theo thứ tự tránh ràng buộc khóa ngoại
        Match.query.delete()
        Team.query.delete()
        Group.query.delete()
        Tournament.query.delete()
        db.session.commit()

        return "✅ Đã xóa toàn bộ dữ liệu trong database."
    except Exception as e:
        db.session.rollback()
        return f"❌ Lỗi khi xóa: {e}", 500

@main.route("/tournament/<int:tournament_id>/knockout", methods=["GET", "POST"])
def view_knockout_bracket(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    matches = Match.query.filter_by(tournament_id=tournament_id, group_id=None).order_by(Match.id).all()

    def winner(m):
        return m.team1 if m.score1 > m.score2 else m.team2 if m.score1 != m.score2 else m.team1

    def loser(m):
        return m.team2 if m.score1 > m.score2 else m.team1 if m.score1 != m.score2 else m.team2

    # ✅ Với 6 đội → có 3 trận: Final, Third, Fifth
    if len(matches) == 3:
        final, third, fifth = matches[:3]

        if request.method == "POST":
            for m in matches:
                s1 = request.form.get(f"score1_{m.id}")
                s2 = request.form.get(f"score2_{m.id}")
                if s1 is not None and s2 is not None and s1.isdigit() and s2.isdigit():
                    m.score1 = int(s1)
                    m.score2 = int(s2)
            db.session.commit()
            return redirect(url_for("main.view_knockout_bracket", tournament_id=tournament_id))

        # ✅ Tính xếp hạng khi đủ điểm
        final_ranking = []
        if all(m.score1 is not None and m.score2 is not None for m in matches):
            final_ranking = [
                {"rank": 1, "name": winner(final)},
                {"rank": 2, "name": loser(final)},
                {"rank": 3, "name": winner(third)},
                {"rank": 4, "name": loser(third)},
                {"rank": 5, "name": winner(fifth)},
                {"rank": 6, "name": loser(fifth)},
            ]

        return render_template("knockout_bracket_6.html",
            tournament=tournament,
            final_match=final,
            third_place_match=third,
            fifth_place_match=fifth,
            final_ranking=final_ranking
        )

    # ✅ Với 8 trận → xử lý như cũ
    elif len(matches) == 8:
        upper = matches[:2]
        lower = matches[2:4]
        final, third, fifth, seventh = matches[4:8]

        if request.method == "POST":
            for m in matches:
                s1 = request.form.get(f"score1_{m.id}")
                s2 = request.form.get(f"score2_{m.id}")
                if s1 is not None and s2 is not None and s1.isdigit() and s2.isdigit():
                    m.score1 = int(s1)
                    m.score2 = int(s2)
            db.session.commit()

            # Cập nhật các trận tiếp theo
            if upper[0].score1 is not None and upper[1].score1 is not None:
                final.team1 = winner(upper[0])
                final.team2 = winner(upper[1])
                third.team1 = loser(upper[0])
                third.team2 = loser(upper[1])

            if lower[0].score1 is not None and lower[1].score1 is not None:
                fifth.team1 = winner(lower[0])
                fifth.team2 = winner(lower[1])
                seventh.team1 = loser(lower[0])
                seventh.team2 = loser(lower[1])

            db.session.commit()
            return redirect(url_for("main.view_knockout_bracket", tournament_id=tournament_id))

        final_ranking = get_final_ranking(tournament.id)
        return render_template("knockout_bracket.html",
            tournament=tournament,
            upper_matches=upper,
            lower_matches=lower,
            final_match=final,
            third_place_match=third,
            fifth_place_match=fifth,
            seventh_place_match=seventh,
            final_ranking=final_ranking
        )

    # ❌ Nếu số lượng trận không hợp lệ
    return "Lỗi: Knock-out chưa được tạo hoặc số lượng trận không hợp lệ.", 400


@main.route("/api/standings/<int:tournament_id>")
def get_standings(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    groups = tournament.groups
    standings_data = {}

    for group in groups:
        standings = calculate_detailed_standings(group)
        standings_data[group.name] = standings

    return {
        "standings": standings_data
    }

@main.route("/update_score", methods=["POST"])
def update_score():
    data = request.get_json()
    match_id = data.get("match_id")
    score1 = data.get("score1")
    score2 = data.get("score2")

    if match_id is None or score1 is None or score2 is None:
        return {"status": "error", "message": "Thiếu dữ liệu."}, 400

    match = Match.query.get_or_404(match_id)
    match.score1 = score1
    match.score2 = score2
    db.session.commit()

    def is_finished(m):
        return m.score1 is not None and m.score2 is not None and m.score1 != m.score2

    def get_winner(m):
        if not is_finished(m):
            return "Đang chờ"
        return m.team1 if m.score1 > m.score2 else m.team2

    def get_loser(m):
        if not is_finished(m):
            return "Đang chờ"
        return m.team2 if m.score1 > m.score2 else m.team1

    # === Nếu là knock-out ===
    if match.group_id is None:
        tournament = match.tournament
        matches = Match.query.filter_by(tournament_id=tournament.id, group_id=None).order_by(Match.id).all()
        updated = []

        try:
            idx = matches.index(match)

            if len(matches) >= 8:
                # 🔁 Giải 8 đội
                if idx == 0:  # upper 1
                    matches[4].team1 = get_winner(match)
                    matches[5].team1 = get_loser(match)
                    updated += [matches[4], matches[5]]
                elif idx == 1:  # upper 2
                    matches[4].team2 = get_winner(match)
                    matches[5].team2 = get_loser(match)
                    updated += [matches[4], matches[5]]
                elif idx == 2:  # lower 1
                    matches[6].team1 = get_winner(match)
                    matches[7].team1 = get_loser(match)
                    updated += [matches[6], matches[7]]
                elif idx == 3:  # lower 2
                    matches[6].team2 = get_winner(match)
                    matches[7].team2 = get_loser(match)
                    updated += [matches[6], matches[7]]

            db.session.commit()

        except Exception as e:
            print("❌ Lỗi cập nhật trận kế tiếp:", e)

        # === Tính bảng xếp hạng cuối cùng ===
        final_ranking = []
        champion_name = None

        if len(matches) >= 8 and all(is_finished(m) for m in matches[4:8]):
            # ✅ Giải 8 đội
            final_ranking = [
                {"rank": 1, "name": get_winner(matches[4])},
                {"rank": 2, "name": get_loser(matches[4])},
                {"rank": 3, "name": get_winner(matches[5])},
                {"rank": 4, "name": get_loser(matches[5])},
                {"rank": 5, "name": get_winner(matches[6])},
                {"rank": 6, "name": get_loser(matches[6])},
                {"rank": 7, "name": get_winner(matches[7])},
                {"rank": 8, "name": get_loser(matches[7])},
            ]
            champion_name = get_winner(matches[4])

        elif len(matches) == 3 and all(is_finished(m) for m in matches):
            # ✅ Giải 6 đội
            final, third, fifth = matches
            final_ranking = [
                {"rank": 1, "name": get_winner(final)},
                {"rank": 2, "name": get_loser(final)},
                {"rank": 3, "name": get_winner(third)},
                {"rank": 4, "name": get_loser(third)},
                {"rank": 5, "name": get_winner(fifth)},
                {"rank": 6, "name": get_loser(fifth)},
            ]
            champion_name = get_winner(final)

        return {
            "status": "ok",
            "updated": "knockout",
            "updated_matches": [
                {
                    "id": m.id,
                    "team1": m.team1,
                    "team2": m.team2,
                    "score1": m.score1,
                    "score2": m.score2
                }
                for m in updated
            ],
            "champion": champion_name,
            "final_ranking": final_ranking
        }

    # === Nếu là vòng bảng ===
    group = match.group
    standings = calculate_detailed_standings(group)
    standings_data = {
        "team_rows": [
            {
                "name": row["name"],
                "match_points": row["match_points"],
                "total_points": row["total_points"],
                "gd": row["gd"]
            }
            for row in standings
        ]
    }

    return {
        "status": "ok",
        "standings": standings_data,
        "group_id": group.id
    }

from flask import jsonify


@main.route("/export_tournament/<int:tournament_id>")
def export_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    groups = Group.query.filter_by(tournament_id=tournament.id).all()

    data = {
        "id": tournament.id,
        "name": tournament.name,
        "groups": []
    }

    for group in groups:
        teams = Team.query.filter_by(group_id=group.id).all()
        matches = Match.query.filter_by(group_id=group.id).all()

        group_data = {
            "name": group.name,
            "teams": [team.name for team in teams],
            "matches": [
                {
                    "team1": m.team1,
                    "team2": m.team2,
                    "score1": m.score1,
                    "score2": m.score2
                }
                for m in matches
            ]
        }
        data["groups"].append(group_data)

    return jsonify(data)
@main.route("/api/groups/add-justin-tuyen-fixed", methods=["POST"])
def add_justin_tuyen_fixed():
    group_id = 98
    group = Group.query.get_or_404(group_id)

    team = Team(name="Justin – Tuyen", tier1="Justin", tier2="Tuyen", group=group)
    db.session.add(team)
    db.session.commit()

    return {
        "status": "success",
        "message": f"✅ Đã thêm đội Justin – Tuyen vào bảng {group.name} (ID: {group.id})."
    }
@main.route("/api/groups/<int:group_id>/regenerate-matches", methods=["POST"])
def regenerate_group_matches(group_id):
    group = Group.query.get_or_404(group_id)

    # ❌ Xóa tất cả trận cũ trong bảng này
    Match.query.filter_by(group_id=group.id).delete()

    teams = group.teams
    if len(teams) < 2:
        return {"status": "error", "message": "❌ Phải có ít nhất 2 đội."}, 400

    # ✅ Tạo lại tất cả cặp trận vòng tròn
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            m = Match(
                group_id=group.id,
                tournament_id=group.tournament_id,
                team1=teams[i].name,
                team2=teams[j].name,
                score1=None,
                score2=None
            )
            db.session.add(m)

    db.session.commit()

    return {
        "status": "success",
        "message": f"✅ Đã tạo {len(teams) * (len(teams) - 1) // 2} trận cho bảng {group.name}."
    }
@main.route("/api/tournament/rename-latest", methods=["POST"])
def rename_latest_tournament():
    latest_tournament = Tournament.query.order_by(Tournament.id.desc()).first()

    if not latest_tournament:
        return {"status": "error", "message": "❌ Không có tournament nào trong database."}, 404

    latest_tournament.name = "Tournament Monday 14th Jul"
    db.session.commit()

    return {
        "status": "success",
        "message": f"✅ Đã đổi tên tournament cuối cùng thành: {latest_tournament.name}",
        "id": latest_tournament.id
    }
@main.route("/api/reset-all-scores", methods=["POST"])
def reset_all_scores():
    try:
        matches = Match.query.all()

        if not matches:
            return {"status": "error", "message": "❌ Không có trận nào trong hệ thống."}, 404

        for match in matches:
            match.score1 = None
            match.score2 = None

        db.session.commit()

        return {
            "status": "success",
            "message": f"✅ Đã đặt lại điểm cho toàn bộ {len(matches)} trận đấu trong hệ thống."
        }

    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"❌ Lỗi: {e}"}, 500
@main.route("/api/rename-justin-tuyen", methods=["POST"])
def rename_justin_tuyen():
    team = Team.query.filter_by(name="Justin – Tuyen").first()

    if not team:
        return {
            "status": "error",
            "message": "❌ Không tìm thấy đội 'Justin – Tuyen'."
        }, 404

    team.name = "Nhân – Tuyền"
    team.tier1 = "Nhân"
    team.tier2 = "Tuyền"

    db.session.commit()

    return {
        "status": "success",
        "message": "✅ Đã đổi tên đội thành 'Nhân – Tuyền'."
    }
@main.route("/delete_tournament/<int:tournament_id>", methods=["POST"])
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)

    # ✅ Lấy danh sách group ID trước khi xóa
    group_ids = [g.id for g in Group.query.filter_by(tournament_id=tournament.id).all()]

    # ✅ Xóa Match trước
    if group_ids:
        Match.query.filter(Match.group_id.in_(group_ids)).delete(synchronize_session=False)
        Team.query.filter(Team.group_id.in_(group_ids)).delete(synchronize_session=False)
        Group.query.filter(Group.id.in_(group_ids)).delete(synchronize_session=False)

    # ✅ Xóa các trận knockout nếu có (không thuộc group)
    Match.query.filter_by(tournament_id=tournament.id).delete(synchronize_session=False)

    # ✅ Cuối cùng mới xóa tournament
    db.session.delete(tournament)
    db.session.commit()

    return redirect(url_for("main.index"))
