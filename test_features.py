"""
Feature test script for TaskFlow2.
Tests all features including the two new ones: Task Status and AI Improve Task.
Run with: venv/Scripts/python test_features.py
"""
import sys
import random
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0
RESULTS = []


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            raw = resp.read()
            if not raw:
                return resp.status, None
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw.decode()
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            detail = json.loads(raw)
        except Exception:
            detail = raw.decode() if raw else str(e)
        return e.code, detail


def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}" + (f"  [{detail}]" if detail else ""))
        FAIL += 1
    RESULTS.append((label, cond))


# ── Health ────────────────────────────────────────────────────────────────────
code, r = req("GET", "/")
check("Health check", code == 200, str(r))

# ── Authentication ────────────────────────────────────────────────────────────
email = f"test_{random.randint(10000,99999)}@test.com"
code, r = req("POST", "/auth/register", {"email": email, "full_name": "Tester", "password": "pass1234"})
check("Registration", code == 201 and "access_token" in r, str(r))
tok = r["access_token"]

code, me = req("GET", "/auth/me", token=tok)
check("Auth /me", code == 200 and me["email"] == email, str(me))

# ── Project CRUD ──────────────────────────────────────────────────────────────
code, proj = req("POST", "/projects/", {"name": "TestProject", "description": "desc"}, tok)
check("Project create", code == 201 and isinstance(proj, dict) and proj.get("id", 0) > 0, str(proj))
pid = proj["id"]

code, pl = req("GET", "/projects/", token=tok)
check("Project list", code == 200 and len(pl) >= 1)

code, pu = req("PUT", f"/projects/{pid}", {"name": "UpdatedProject", "description": "new"}, tok)
check("Project update", code == 200 and pu["name"] == "UpdatedProject", str(pu))

# ── Task CRUD + Default Status ────────────────────────────────────────────────
code, tk = req("POST", "/tasks/", {"title": "My Task", "description": "d", "priority": "medium", "project_id": pid}, tok)
check("Task create", code == 201 and tk["id"] > 0, str(tk))
check("Task default status = todo", tk.get("status") == "todo", f"got status={tk.get('status')}")
tid = tk["id"]

code, tu = req("PUT", f"/tasks/{tid}", {"title": "Updated Task", "priority": "high", "status": "in_progress", "project_id": pid}, tok)
check("Task update (title)", code == 200 and tu["title"] == "Updated Task", str(tu))
check("Task update (status via PUT)", tu.get("status") == "in_progress", f"got={tu.get('status')}")

# ── Status PATCH ──────────────────────────────────────────────────────────────
code, tp = req("PATCH", f"/tasks/{tid}/status", {"status": "completed"}, tok)
check("Task PATCH status → completed", code == 200 and tp.get("status") == "completed", f"got={tp.get('status')}")

# ── Status persistence (GET after PATCH) ─────────────────────────────────────
code, tg = req("GET", f"/tasks/{tid}", token=tok)
check("Status persists after GET", tg.get("status") == "completed", f"got={tg.get('status')}")

# ── Status Counts endpoint ────────────────────────────────────────────────────
code, sc = req("GET", "/tasks/status-counts", token=tok)
check("Status counts – HTTP 200",       code == 200, f"code={code}")
check("Status counts – todo key",       "todo"        in sc, str(sc))
check("Status counts – in_progress key","in_progress" in sc, str(sc))
check("Status counts – completed key",  "completed"   in sc, str(sc))
check("Status counts – completed >= 1", sc.get("completed", 0) >= 1, str(sc))

# ── To Do → In Progress → Completed flow ─────────────────────────────────────
code, tk2 = req("POST", "/tasks/", {"title": "FlowTask", "priority": "medium", "project_id": pid}, tok)
tid2 = tk2["id"]
check("New task starts as todo", tk2.get("status") == "todo")

code, _ = req("PATCH", f"/tasks/{tid2}/status", {"status": "in_progress"}, tok)
code, tg2 = req("GET", f"/tasks/{tid2}", token=tok)
check("todo → in_progress persists", tg2.get("status") == "in_progress")

code, _ = req("PATCH", f"/tasks/{tid2}/status", {"status": "completed"}, tok)
code, tg3 = req("GET", f"/tasks/{tid2}", token=tok)
check("in_progress → completed persists", tg3.get("status") == "completed")

# ── Search ────────────────────────────────────────────────────────────────────
code, st = req("POST", "/tasks/", {"title": "SearchableTask", "priority": "low", "project_id": pid}, tok)

code, s1 = req("GET", "/tasks/search?title=SearchableTask&algo=binary", token=tok)
check("Binary search", code == 200 and s1.get("title") == "SearchableTask", str(s1))

code, s2 = req("GET", "/tasks/search?title=SearchableTask&algo=linear", token=tok)
check("Linear search", code == 200 and s2.get("title") == "SearchableTask", str(s2))

# ── Priority Sort ─────────────────────────────────────────────────────────────
code, sorted_tasks = req("GET", "/tasks?sort=priority", token=tok)
check("Priority sort – returns list", code == 200 and isinstance(sorted_tasks, list) and len(sorted_tasks) >= 1)

# ── AI Quick Add ─────────────────────────────────────────────────────────────
code, qa = req("POST", "/tasks/quick-add", {"text": "fix login bug urgently", "project_id": pid}, tok)
check("AI Quick Add – task created",    code == 201 and qa["id"] > 0, str(qa))
check("AI Quick Add – high priority",   qa.get("priority") == "high", f"got={qa.get('priority')}")
check("AI Quick Add – default todo",    qa.get("status") == "todo", f"got={qa.get('status')}")
check("AI Quick Add – title non-empty", len(qa.get("title", "")) > 0)

# ── AI Improve Task ───────────────────────────────────────────────────────────
# Category 1: React (Hindi input)
code, i1 = req("POST", "/tasks/improve", {"title": "react padhna hai", "priority": "medium"}, tok)
check("Improve React – HTTP 200",         code == 200, f"code={code} body={i1}")
check("Improve React – title changed",    i1.get("title") != "react padhna hai", f"title={i1.get('title')}")
check("Improve React – description set",  len(i1.get("description") or "") > 0, f"desc={i1.get('description')}")

# Category 2: Docker
code, i2 = req("POST", "/tasks/improve", {"title": "learn docker", "priority": "medium"}, tok)
check("Improve Docker – title changed",   i2.get("title") != "learn docker", f"title={i2.get('title')}")
check("Improve Docker – description set", len(i2.get("description") or "") > 0)

# Category 3: DBMS interview
code, i3 = req("POST", "/tasks/improve", {"title": "prepare for dbms interview", "priority": "medium"}, tok)
check("Improve DBMS – title changed",     i3.get("title") != "prepare for dbms interview", f"title={i3.get('title')}")
check("Improve DBMS – description set",   len(i3.get("description") or "") > 0)

# Category 4: due date
code, i4 = req("POST", "/tasks/improve", {"title": "fix login bug tomorrow", "due_date": "tomorrow", "priority": "medium"}, tok)
check("Improve – due date preserved",     i4.get("due_date") is not None, f"due={i4.get('due_date')}")

# Category 5: Python
code, i5 = req("POST", "/tasks/improve", {"title": "learn python", "priority": "medium"}, tok)
check("Improve Python – title changed",   i5.get("title") != "learn python", f"title={i5.get('title')}")
check("Improve Python – description set", len(i5.get("description") or "") > 0)

# Category 6: Portfolio website
code, i6 = req("POST", "/tasks/improve", {"title": "build portfolio website", "priority": "low"}, tok)
check("Improve Portfolio – title changed",    i6.get("title") != "build portfolio website", f"title={i6.get('title')}")
check("Improve Portfolio – description set",  len(i6.get("description") or "") > 0)

# ── Task Delete ───────────────────────────────────────────────────────────────
code, _ = req("DELETE", f"/tasks/{tid}", token=tok)
check("Task delete", code == 204, f"code={code}")

# Verify deleted
code2, _ = req("GET", f"/tasks/{tid}", token=tok)
check("Task deleted – 404 on GET", code2 == 404)

# ── Dashboard / Project Statistics ───────────────────────────────────────────
code, stats = req("GET", "/projects/statistics", token=tok)
check("Project statistics", code == 200 and isinstance(stats, list))

# ── Project Delete ────────────────────────────────────────────────────────────
code, _ = req("DELETE", f"/projects/{pid}", token=tok)
check("Project delete", code == 204, f"code={code}")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 50)
print(f"  TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 50)
sys.exit(0 if FAIL == 0 else 1)
