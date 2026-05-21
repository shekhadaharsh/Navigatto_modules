# 🌿 Git Branching Strategy — Navigaatto Modules

## 3-Person Team | Same Repo | Different Machines

---

## Branch Structure

```
main              ← ✅ Stable, tested, demo-ready code ONLY
└── dev           ← 🔀 Integration branch (all modules merge here first)
    ├── feature/driver-module      ← Person 1 (Harsh) — Driver Behaviour
    ├── feature/fuel-module        ← Person 2 — Fuel & Theft Detection
    └── feature/maintenance-module ← Person 3 — Maintenance Alerts
```

---

## Daily Workflow (Har Din)

### 1. Kaam shuru karne se pehle — apni branch update karo
```bash
git checkout feature/driver-module   # apni branch
git fetch origin
git merge origin/dev                  # dev se latest lelo
```

### 2. Kaam karo, commit karo
```bash
git add .
git commit -m "feat(driver): add leaderboard pagination"
```

### 3. Push karo
```bash
git push origin feature/driver-module
```

### 4. Jab module ready ho → Pull Request banao: `feature/xxx` → `dev`
- GitHub pe jao → New Pull Request
- Base: `dev` ← Compare: `feature/driver-module`
- Dono log review karein → Merge karo

### 5. Sab modules ready hone pe: `dev` → `main` merge

---

## Commit Message Convention

```
feat(driver):     naya kaam — driver module
feat(fuel):       naya kaam — fuel module
feat(maintenance): naya kaam — maintenance module
fix(driver):      bug fix
refactor:         code cleanup
docs:             documentation update
```

---

## Branch Setup (Pehli Baar — Ek Baar Karo)

```bash
# Person 1 (Harsh) — Driver Module
git checkout -b feature/driver-module
git push -u origin feature/driver-module

# Person 2 — Fuel Module
git checkout -b feature/fuel-module
git push -u origin feature/fuel-module

# Person 3 — Maintenance Module
git checkout -b feature/maintenance-module
git push -u origin feature/maintenance-module

# Dev branch banao (ek baar main se)
git checkout main
git checkout -b dev
git push -u origin dev
```

---

## Golden Rules 🔒

| ❌ Kabhi Mat Karo | ✅ Hamesha Karo |
|---|---|
| Directly `main` pe push | Feature branch use karo |
| Dusre ka module edit karo | Apna module sirf touch karo |
| `git push --force` | Normal push karo |
| `dev` pe directly kaam karo | Feature branch se PR banao |

---

## Module Boundaries — Kaun Kya Touch Karta Hai

| Person | Branch | Files |
|---|---|---|
| Person 1 (Harsh) | `feature/driver-module` | `backend/driver_module/*`, `frontend/src/` (driver section) |
| Person 2 | `feature/fuel-module` | `backend/fuel_module/*`, `frontend/src/` (fuel card) |
| Person 3 | `feature/maintenance-module` | `backend/maintenance_module/*`, `frontend/src/` (maintenance card) |
| All | `frontend/src/App.jsx` | **COORDINATE** before editing — avoid conflicts |

---

## How Modules Combine in Frontend

`main.py` mein sirf uncomment karo jab module ready ho:

```python
# main.py
app.include_router(driver_router)         # ✅ Person 1 — DONE
# app.include_router(fuel_router)         # ⬜ Person 2 — uncomment when ready
# app.include_router(maint_router)        # ⬜ Person 3 — uncomment when ready
```

Backend endpoint `/drivers/{id}/trips/{trip_id}/details` already combines:
- ✅ Driver Score (Person 1)
- 🔄 Fuel & Theft data (Person 2 upgrades their section)
- 🔄 Maintenance alerts (Person 3 upgrades their section)
