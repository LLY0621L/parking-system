import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DATABASE = "parking.db"

# 停车场配置
TOTAL_SPOTS = 12
NORMAL_SPOTS = 10
SPECIAL_SPOTS = 2
SPOT_LAYOUT = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
SPECIAL_SPOT_IDS = [11, 12]
FREE_MINUTES = 30
RATE_PER_HOUR = 5
RESERVE_TIMEOUT = 15


# 数据库连接
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# 初始化数据库（🔥 我已修复这里，保证车位一定可用）
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS spots
                 (id INTEGER PRIMARY KEY,type TEXT,status TEXT,
                  is_reserved INTEGER,reserved_time TEXT,plate TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,plate TEXT,spot_id INTEGER,
                  is_special INTEGER,entry_time TEXT,exit_time TEXT,
                  duration REAL,fee REAL,paid INTEGER)''')

    # 🔥 修复：每次启动都重置车位为可用状态
    c.execute("DELETE FROM spots")
    for i in range(1, 13):
        t = "special" if i in SPECIAL_SPOT_IDS else "normal"
        c.execute("INSERT INTO spots (id,type,status,is_reserved) VALUES (?,?,?,0)",
                  (i, t, "available"))

    conn.commit()
    conn.close()


# 找最近车位（入口在左，优先左列）
def find_nearest_spot(is_special=False):
    conn = get_db()
    c = conn.cursor()
    if is_special:
        c.execute("SELECT id FROM spots WHERE type='special' AND status='available' AND is_reserved=0")
    else:
        c.execute("SELECT id FROM spots WHERE type='normal' AND status='available' AND is_reserved=0")
    res = [r["id"] for r in c.fetchall()]
    conn.close()
    if not res: return None

    def dist(s):
        for i, row in enumerate(SPOT_LAYOUT):
            if s in row: return row.index(s) * 100 + i
        return 999

    res.sort(key=dist)
    return res[0]


# 计费
def calc_fee(ent, ext, special):
    if special: return 0.0
    sec = (ext - ent).total_seconds()
    min = sec / 60
    if min <= FREE_MINUTES: return 0.0
    h = int(min / 60)
    if min % 60 > 0: h += 1
    return h * RATE_PER_HOUR


# 释放超时预约
def release_expired():
    conn = get_db()
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute("SELECT id,reserved_time FROM spots WHERE is_reserved=1")
    for r in c.fetchall():
        try:
            t = datetime.datetime.strptime(r["reserved_time"], "%Y-%m-%d %H:%M:%S")
            if (now - t).total_seconds() / 60 > RESERVE_TIMEOUT:
                c.execute('''UPDATE spots SET status="available",
                             is_reserved=0,reserved_time=NULL,plate=NULL WHERE id=?''', (r["id"],))
        except:
            pass
    conn.commit()
    conn.close()


# 页面路由
@app.route('/')
def index():
    release_expired()
    return render_template('index.html')


@app.route('/reserve', methods=['POST'])
def reserve():
    p = request.form.get('plate', '').strip()
    s = int(request.form.get('special', 0))
    if not p: return jsonify({"code": 1, "msg": "请输入车牌"})
    release_expired()
    spot = find_nearest_spot(s)
    if not spot: return jsonify({"code": 1, "msg": "无可用车位"})
    conn = get_db()
    c = conn.cursor()
    c.execute('''UPDATE spots SET status="reserved",is_reserved=1,
                 reserved_time=?,plate=? WHERE id=?''',
              (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), p, spot))
    conn.commit()
    conn.close()
    return jsonify({"code": 0, "msg": f"预约成功 车位{spot}", "spot": spot})


@app.route('/enter', methods=['POST'])
def enter():
    p = request.form.get('plate', '').strip()
    s = int(request.form.get('special', 0))
    if not p: return jsonify({"code": 1, "msg": "请输入车牌"})
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM spots WHERE plate=? AND is_reserved=1", (p,))
    r = c.fetchone()
    if r:
        spot = r["id"]
    else:
        spot = find_nearest_spot(s)
        if not spot:
            conn.close()
            return jsonify({"code": 1, "msg": "车位已满"})
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''UPDATE spots SET status="occupied",is_reserved=0,
                 reserved_time=NULL,plate=? WHERE id=?''', (p, spot))
    c.execute('''INSERT INTO records (plate,spot_id,is_special,entry_time)
                 VALUES (?,?,?,?)''', (p, spot, s, now))
    conn.commit()
    conn.close()
    return jsonify({"code": 0, "msg": f"入场成功 车位{spot}", "spot": spot})



@app.route('/exit', methods=['POST'])
def exit_park():
    p = request.form.get('plate', '').strip()
    if not p:
        return jsonify({"code": 1, "msg": "请输入车牌"})

    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT * FROM records WHERE plate=? AND exit_time IS NULL ORDER BY entry_time DESC LIMIT 1''', (p,))
    r = c.fetchone()

    if not r:
        conn.close()
        return jsonify({"code": 1, "msg": "无入场记录"})

    ent = datetime.datetime.strptime(r["entry_time"], "%Y-%m-%d %H:%M:%S")
    ext = datetime.datetime.now()
    fee = calc_fee(ent, ext, r["is_special"])
    dur = round((ext - ent).total_seconds() / 3600, 2)

    c.execute('''UPDATE records SET exit_time=?, duration=?, fee=?, paid=1 WHERE id=?''',
              (ext.strftime("%Y-%m-%d %H:%M:%S"), dur, fee, r["id"]))

    c.execute('''UPDATE spots SET status="available", plate=NULL WHERE id=?''', (r["spot_id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "code": 0,
        "msg": "离场成功",
        "entry_time": r["entry_time"],
        "exit_time": ext.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": round((ext - ent).total_seconds() / 60, 2),  # 分钟
        "fee": fee,
        "is_special": r["is_special"]
    })

@app.route('/spot')
def spot():
    release_expired()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM spots ORDER BY id")
    spots = [dict(x) for x in c.fetchall()]
    conn.close()
    return jsonify({"layout": SPOT_LAYOUT, "spots": spots, "special": SPECIAL_SPOT_IDS})


@app.route('/find_car', methods=['POST'])
def find_car():
    p = request.form.get('plate', '').strip()
    if not p:
        return jsonify({"code": 1, "msg": "请输入车牌"})
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT spot_id FROM records 
                 WHERE plate=? AND exit_time IS NULL 
                 ORDER BY entry_time DESC LIMIT 1''', (p,))
    r = c.fetchone()
    conn.close()
    if r:
        return jsonify({"code": 0, "msg": f"您的车辆停在车位 {r['spot_id']}", "spot": r['spot_id']})
    else:
        return jsonify({"code": 1, "msg": "未找到您的车辆记录"})


@app.route('/records')
def records():
    return render_template('records.html')


@app.route('/api/records')
def api_records():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM records ORDER BY id DESC")
    data = [dict(x) for x in c.fetchall()]
    conn.close()
    return jsonify(data)


@app.route('/stats')
def stats():
    return render_template('stats.html')


@app.route('/api/stats')
def api_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt,SUM(fee) as total FROM records WHERE paid=1")
    total = dict(c.fetchone())
    c.execute('''SELECT strftime('%Y-%m-%d',entry_time) d,
                 COUNT(*) c,SUM(fee) s FROM records WHERE paid=1 GROUP BY d ORDER BY d''')
    daily = [dict(x) for x in c.fetchall()]
    conn.close()
    return jsonify({"total": total, "daily": daily})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)