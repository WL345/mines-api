from fastapi import FastAPI, Query, Body, HTTPException
from fastapi.responses import JSONResponse
import json, sqlite3

app = FastAPI()

APPS_DATA_FILE = "app_ids.db"
CORRECT_API_KEY = "SecurePassword"


@app.get("/apps/check")  # Get info based on user
def check_has_applied(user_id=Query(...)):
    try:
        conn = sqlite3.connect(APPS_DATA_FILE)
        cursor = conn.cursor()

        has_tester = False
        has_mod = False

        cursor.execute("SELECT 1 FROM tester_apps WHERE USER_ID = ?", (user_id,))
        if cursor.fetchone():
            has_tester = True

        cursor.execute("SELECT 1 FROM mod_apps WHERE USER_ID = ?", (user_id,))
        if cursor.fetchone():
            has_mod = True

        conn.close()
        return {
            "user_id": user_id,
            "has_tester": has_tester,
            "has_mod": has_mod
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/apps/log")  # Create a log for a user
def log_application(user_id=Body(...), type_=Body(...)):
    conn = sqlite3.connect(APPS_DATA_FILE)
    cursor = conn.cursor()
    user_id = str(user_id)

    if type_ == "tester":
        cursor.execute('''
        INSERT INTO tester_apps (USER_ID) 
        VALUES (?)
        ''', (user_id, ))

    elif type_ == "mod":
        cursor.execute('''
        INSERT INTO mod_apps (USER_ID)
        VALUES (?)
        ''', (user_id, ))

    else:
        return JSONResponse(content={"message": "Incorrect type_"}, status_code=422)

    conn.commit()
    conn.close()
    return JSONResponse(content={"message": "Entry created successfully"}, status_code=200)


@app.get("/apps/setup")
def setup_training(api_key: str = Query(...)):
    if api_key != CORRECT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    conn = sqlite3.connect(APPS_DATA_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mod_apps (
        USER_ID TEXT
    )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tester_apps (
        USER_ID TEXT
    )''')
    conn.commit()

    try:
        with open("saved_user_ids.txt", "r") as f:
            data = json.load(f)

        for row in data.get("mod_apps", []):
            cursor.execute('''
                INSERT INTO mod_apps (USER_id)
                VALUES (?)
            ''', (row, ))

        for row in data.get("tester_apps", []):
            cursor.execute('''
                INSERT INTO tester_apps (USER_id)
                VALUES (?)
            ''', (row, ))

        conn.commit()
        conn.close()
        return JSONResponse(content={"message": "Database initialized and data imported.", "data": data})
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


@app.get("/apps/view-all")
def view_all_apps(api_key: str = Query(...)):
    if api_key != CORRECT_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    try:
        # Connect to the database
        conn = sqlite3.connect(APPS_DATA_FILE)
        cursor = conn.cursor()

        # Execute a query to retrieve all rows
        cursor.execute('SELECT * FROM mod_apps')
        mod_app_rows = cursor.fetchall()
        cursor.execute('SELECT * FROM tester_apps')
        tester_app_rows = cursor.fetchall()
        conn.close()

        # If there are entries, return them; otherwise, return a message
        mod_apps = []
        tester_apps = []

        for user_id in mod_app_rows:
            mod_apps.append(user_id[0])
        for user_id in tester_app_rows:
            tester_apps.append(user_id[0])

        if mod_apps or tester_apps:
            return JSONResponse(content={"mod_apps": mod_apps, "tester_apps": tester_apps})
        else:
            return JSONResponse(content={"message": "No entries found"}, status_code=404)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/apps/delete-all")
def delete_all_apps(api_key: str = Query(...)):
    if api_key != "qwe1234":
        raise HTTPException(status_code=403, detail="Invalid API key")

    try:
        conn = sqlite3.connect(APPS_DATA_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mod_apps")
        cursor.execute("DELETE FROM tester_apps")
        conn.commit()
        conn.close()
        return {"message": "All entries deleted successfully."}
    except Exception as e:
        return {"error": str(e)}
