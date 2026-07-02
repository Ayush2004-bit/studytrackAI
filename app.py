from flask import Flask, render_template, request, redirect, session, url_for
import pandas as pd
import numpy as np
import ast

app = Flask(__name__)
app.secret_key = "studytrack_secret"

def ai_chat_response(student, message):
    message = message.lower()
    responses = []

    # Performance
    if "score" in message or "marks" in message:
        if student["Total_Score"] < 60:
            responses.append("Your score is below average. Focus on revision and practice tests.")
        else:
            responses.append("Your academic performance is good. Maintain consistency.")

    # Study habits
    if "study" in message or "hours" in message:
        if student["Study_Hours_per_Week"] < 10:
            responses.append("Increase your study hours gradually for better results.")
        else:
            responses.append("Your study hours are sufficient. Focus on quality study.")

    # Stress
    if "stress" in message or "pressure" in message:
        if student["Stress_Level (1-10)"] > 7:
            responses.append("Your stress level is high. Try meditation and better time management.")
        else:
            responses.append("Your stress level is manageable. Keep a balanced routine.")

    # Sleep
    if "sleep" in message:
        if student["Sleep_Hours_per_Night"] < 6:
            responses.append("Improve sleep to enhance memory and focus.")
        else:
            responses.append("Your sleep routine looks healthy.")

    # Cluster-based intelligence
    responses.append(
        f"Based on Cluster {int(student['KMeans_Cluster'])}, students like you perform better with structured schedules."
    )

    if not responses:
        responses.append("I can help you with study habits, stress, sleep, or performance insights.")

    return " ".join(responses)

# =====================================================
# LOAD DATA
# =====================================================
df = pd.read_csv("model/recommendation_ready_students.csv")

# Fix column names (IMPORTANT)
df.columns = df.columns.str.strip()

df["Recommendations"] = df["Recommendations"].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) else x
)

# =====================================================
# CLUSTER INSIGHTS
# =====================================================
cluster_insights = {
    0: {"title": "Struggling Learners", "color": "danger",
        "description": "Low study hours, high distractions."},
    1: {"title": "Overworked & Stressed", "color": "warning",
        "description": "High effort but poor balance."},
    2: {"title": "High Performers", "color": "success",
        "description": "Excellent habits and outcomes."},
    3: {"title": "Irregular Attendees", "color": "info",
        "description": "Low attendance and routine."}
}

# =====================================================
# DEMO AUTH
# =====================================================
users = {"admin": "admin123"}

# =====================================================
# AI COMPARISON ENGINE
# =====================================================
def generate_ai_recommendation(a, b):
    recs = []

    if a["KMeans_Cluster"] == b["KMeans_Cluster"]:
        recs.append("Both students are in the same learning cluster. Peer learning is recommended.")
    else:
        recs.append("Students belong to different clusters. Lower performer can adopt better habits.")

    if a["Total_Score"] > b["Total_Score"]:
        recs.append("Student B should increase focused study hours.")
    else:
        recs.append("Student A should improve consistency.")

    if a["Attendance (%)"] < b["Attendance (%)"]:
        recs.append("Student A should improve attendance.")
    elif b["Attendance (%)"] < a["Attendance (%)"]:
        recs.append("Student B should improve attendance.")

    if a["Stress_Level (1-10)"] > b["Stress_Level (1-10)"]:
        recs.append("Student A should reduce stress via better sleep and breaks.")
    elif b["Stress_Level (1-10)"] > a["Stress_Level (1-10)"]:
        recs.append("Student B shows higher stress and needs balance.")

    return recs

# =====================================================
# ROUTES
# =====================================================
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if users.get(request.form["username"]) == request.form["password"]:
            session["logged_in"] = True
            return redirect("/dashboard")
        error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    student_ids = df["Student_ID"].tolist()
    student_data = None
    cluster_info = None
    recommendations = []

    if request.method == "POST":
        sid = request.form.get("student_id")
        row = df[df["Student_ID"] == sid]

        if not row.empty:
            student_data = row.iloc[0]
            cluster_info = cluster_insights[int(student_data["KMeans_Cluster"])]
            recommendations = student_data["Recommendations"]

    cluster_counts = df["KMeans_Cluster"].value_counts().sort_index().to_dict()

    return render_template(
        "dashboard.html",
        student_ids=student_ids,
        student_data=student_data,
        cluster_info=cluster_info,
        recommendations=recommendations,
        cluster_counts=cluster_counts
    )

# ---------------- STUDENTS LIST ----------------
@app.route("/students")
def students():
    return render_template(
        "students.html",
        students=df.to_dict(orient="records")
    )

# ---------------- STUDENT PROFILE (FIXED) ----------------
@app.route("/student/<sid>")
def student_profile(sid):
    row = df[df["Student_ID"] == sid]

    if row.empty:
        return "Student not found", 404

    student = row.iloc[0]
    cluster_info = cluster_insights[int(student["KMeans_Cluster"])]

    return render_template(
        "student_profile.html",
        student=student,
        cluster_info=cluster_info
    )

# ---------------- PERFORMANCE ----------------
@app.route("/performance")
def performance():
    return render_template(
        "performance.html",
        scores=df["Total_Score"].tolist(),
        attendance=df["Attendance (%)"].tolist()
    )

# ---------------- AI COMPARISON ----------------
@app.route("/comparison", methods=["GET", "POST"])
def comparison():
    student_ids = df["Student_ID"].tolist()
    student_a = student_b = None
    cluster_a = cluster_b = None
    ai_recommendations = []

    if request.method == "POST":
        a = request.form.get("student_a")
        b = request.form.get("student_b")

        ra = df[df["Student_ID"] == a]
        rb = df[df["Student_ID"] == b]

        if not ra.empty and not rb.empty:
            student_a = ra.iloc[0]
            student_b = rb.iloc[0]

            cluster_a = cluster_insights[int(student_a["KMeans_Cluster"])]
            cluster_b = cluster_insights[int(student_b["KMeans_Cluster"])]

            ai_recommendations = generate_ai_recommendation(student_a, student_b)

    return render_template(
        "comparison.html",
        student_ids=student_ids,
        student_a=student_a,
        student_b=student_b,
        cluster_a=cluster_a,
        cluster_b=cluster_b,
        ai_recommendations=ai_recommendations
    )

# ---------------- CLUSTERS ----------------
@app.route("/clusters")
def clusters():
    return render_template("clusters.html", cluster_insights=cluster_insights)

# ---------------- STUDY HABITS (CHART) ----------------
@app.route("/habits")
def habits():
    # Average study hours per cluster
    habit_data = (
        df.groupby("KMeans_Cluster")["Study_Hours_per_Week"]
        .mean()
        .round(2)
        .to_dict()
    )

    labels = [f"Cluster {k}" for k in habit_data.keys()]
    values = list(habit_data.values())

    return render_template(
        "habits.html",
        labels=labels,
        values=values
    )
# ---------------- LIFESTYLE ANALYSIS ----------------
@app.route("/lifestyle")
def lifestyle():
    lifestyle_data = (
        df.groupby("KMeans_Cluster")[["Sleep_Hours_per_Night", "Stress_Level (1-10)"]]
        .mean()
        .round(2)
        .reset_index()
    )

    clusters = lifestyle_data["KMeans_Cluster"].tolist()
    sleep_hours = lifestyle_data["Sleep_Hours_per_Night"].tolist()
    stress_levels = lifestyle_data["Stress_Level (1-10)"].tolist()

    return render_template(
        "lifestyle.html",
        clusters=clusters,
        sleep_hours=sleep_hours,
        stress_levels=stress_levels
    )
# ---------------- RECOMMENDATIONS ----------------
@app.route("/recommendations")
def recommendations():
    cluster_summary = (
        df.groupby("KMeans_Cluster")[[
            "Total_Score",
            "Attendance (%)",
            "Study_Hours_per_Week",
            "Sleep_Hours_per_Night",
            "Stress_Level (1-10)"
        ]]
        .mean()
        .round(2)
        .reset_index()
    )

    recs = []

    for _, row in cluster_summary.iterrows():
        suggestions = []

        if row["Total_Score"] < 60:
            suggestions.append("Increase daily study consistency and revise fundamentals.")

        if row["Attendance (%)"] < 75:
            suggestions.append("Improve attendance to strengthen academic performance.")

        if row["Study_Hours_per_Week"] < 10:
            suggestions.append("Increase weekly study hours gradually.")

        if row["Sleep_Hours_per_Night"] < 6:
            suggestions.append("Improve sleep routine for better focus.")

        if row["Stress_Level (1-10)"] > 7:
            suggestions.append("Practice stress management techniques like meditation.")

        if not suggestions:
            suggestions.append("Maintain current habits and performance.")

        recs.append({
            "cluster": int(row["KMeans_Cluster"]),
            "recommendations": suggestions
        })

    return render_template("recommendations.html", recs=recs)


@app.route("/ai-chat/<sid>", methods=["GET", "POST"])
def ai_chat(sid):
    student = df[df["Student_ID"] == sid]

    if student.empty:
        return "Student Not Found", 404

    s = student.iloc[0]
    reply = None

    if request.method == "POST":
        user_message = request.form.get("message")
        reply = ai_chat_response(s, user_message)

    return render_template(
        "ai_chat.html",
        student=s,
        reply=reply
    )

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
