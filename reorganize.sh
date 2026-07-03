#!/bin/bash
set -e

echo "Starting reorganization..."

# 1. API Restructure
mkdir -p api/app/routes api/app/core api/app/schemas api/app/services api/app/middleware api/app/tasks
touch api/app/__init__.py api/app/routes/__init__.py api/app/core/__init__.py api/app/schemas/__init__.py api/app/services/__init__.py api/app/middleware/__init__.py api/app/tasks/__init__.py

mv api/main.py api/app/ 2>/dev/null || true
mv api/routes/* api/app/routes/ 2>/dev/null || true
mv api/models/* api/app/schemas/ 2>/dev/null || true
mv api/services/* api/app/services/ 2>/dev/null || true
mv api/middleware/* api/app/middleware/ 2>/dev/null || true
mv api/tasks/* api/app/tasks/ 2>/dev/null || true

# Cleanup empty api dirs
rm -d api/routes api/models api/services api/middleware api/tasks 2>/dev/null || true

# 2. SRC Restructure
mkdir -p src/absa src/languages/english src/languages/hindi src/languages/hinglish src/models src/utils
touch src/absa/__init__.py src/languages/__init__.py src/languages/english/__init__.py src/languages/hindi/__init__.py src/languages/hinglish/__init__.py src/models/__init__.py src/utils/__init__.py

# Move items in src to their respective folders (will do this manually or cautiously later, right now let's just create the folders)
# Since I need to check what exists in src/ before moving.

# 3. ML Restructure
mkdir -p ml/experiments ml/notebooks ml/configs ml/training
mv mlflow ml/experiments/ 2>/dev/null || true
mv mlruns ml/experiments/ 2>/dev/null || true
mv notebooks/* ml/notebooks/ 2>/dev/null || true
rm -d notebooks 2>/dev/null || true

# 4. Docs Restructure
mkdir -p docs/architecture docs/ml docs/api docs/planning docs/guides
mv .planning/* docs/planning/ 2>/dev/null || true
rm -d .planning 2>/dev/null || true

echo "Reorganization completed."
