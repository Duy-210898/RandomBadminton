from flask import Flask, render_template, request, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

# === Bước 1: Nhập danh sách và ghép đội ===
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_tier1 = request.form.get("tier1", "")
        raw_tier2 = request.form.get("tier2", "")

        tier1 = [x.strip() for x in raw_tier1.split("\n") if x.strip()]
        tier2 = [x.strip() for x in raw_tier2.split("\n") if x.strip()]

        if len(tier1) != len(tier2):
            return render_template("index.html", error="Số lượng Tier 1 và Tier 2 phải bằng nhau.")

        random.shuffle(tier1)
        random.shuffle(tier2)

        combined = list(zip(tier1, tier2))
        session["teams"] = combined 
        return redirect(url_for("show_teams"))

    return render_template("index.html")

# === Bước 2: Hiển thị danh sách đội sau khi ghép ===
@app.route("/show_teams")
def show_teams():
    teams = session.get("teams", [])
    return render_template("show_teams.html", teams=teams)

@app.route("/assign_groups", methods=["POST"])
def assign_groups():
    num_groups = int(request.form.get("num_groups"))
    teams = list(session.get("teams", []))
    random.shuffle(teams)

    groups = {f"Group {chr(65+i)}": [] for i in range(num_groups)}
    for idx, team in enumerate(teams):
        group_name = f"Group {chr(65 + (idx % num_groups))}"
        groups[group_name].append(team)

    session["groups"] = groups

    def round_robin(teams):
        matches = []
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                team1 = f"{teams[i][0]} – {teams[i][1]}"
                team2 = f"{teams[j][0]} – {teams[j][1]}"
                matches.append((team1, team2))
        return matches

    schedule = {group: round_robin(teams) for group, teams in groups.items()}

    return render_template("group_result.html", groups=groups, schedule=schedule)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
