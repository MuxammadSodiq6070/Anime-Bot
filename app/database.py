import sqlite3
from datetime import datetime, date


class Database:
    def __init__(self, db_name='anime_bot.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        # ── Users ──────────────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT, first_name TEXT, last_name TEXT,
            status       TEXT    DEFAULT 'Simple',
            balance      INTEGER DEFAULT 0,
            vip_time     TEXT    DEFAULT '00.00.0000 00:00',
            language     TEXT    DEFAULT 'uz',
            referral_by  INTEGER DEFAULT NULL,
            coins        INTEGER DEFAULT 0,
            streak       INTEGER DEFAULT 0,
            last_seen    TEXT    DEFAULT NULL,
            ab_group     TEXT    DEFAULT 'A',
            created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        )''')

        # ── Anime ──────────────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS anime (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            episode     INTEGER DEFAULT 1,
            country     TEXT, language TEXT, image TEXT,
            description TEXT, genre TEXT,
            rating      REAL    DEFAULT 0.0,
            status      TEXT    DEFAULT 'ongoing',
            views       INTEGER DEFAULT 0,
            is_vip      INTEGER DEFAULT 0,
            early_access INTEGER DEFAULT 0,
            create_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        )''')

        # ── Anime episodes ─────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS anime_episodes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id       INTEGER, episode_number INTEGER, file_id TEXT,
            created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        # ── Anime clips (Shorts) ───────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS anime_clips (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id   INTEGER,
            file_id    TEXT,
            caption    TEXT,
            views      INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        # ── Channels ───────────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS channels (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id   TEXT UNIQUE, channel_link TEXT,
            channel_type TEXT DEFAULT 'request'
        )''')

        # ── Payments ───────────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, amount INTEGER, photo TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        # ── Bot settings ───────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY, value TEXT
        )''')

        # ── Ratings & Reviews ──────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS anime_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER, user_id INTEGER,
            rating INTEGER, review TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(anime_id, user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id),
            FOREIGN KEY (user_id)  REFERENCES users (user_id)
        )''')

        # ── Watch progress ─────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS watch_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, anime_id INTEGER,
            episode_number INTEGER DEFAULT 1,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_id),
            FOREIGN KEY (user_id)  REFERENCES users (user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        # ── Watchlist ──────────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, anime_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_id),
            FOREIGN KEY (user_id)  REFERENCES users (user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        # ── Scheduled posts ────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER, channel TEXT,
            scheduled_at TEXT, sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        # ── Genre preferences ──────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS user_genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, genre TEXT,
            UNIQUE(user_id, genre),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        # ── Daily missions ─────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS daily_missions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            mission_key TEXT,
            progress    INTEGER DEFAULT 0,
            completed   INTEGER DEFAULT 0,
            date        TEXT DEFAULT (date('now')),
            UNIQUE(user_id, mission_key, date),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        # ── Coin transactions ──────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS coin_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            amount      INTEGER,
            reason      TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        # ── A/B test events ────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS ab_events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            ab_group   TEXT,
            event      TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        # ── AI chat history ────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS ai_chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            role       TEXT,
            content    TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        # ── Default settings ───────────────────────────────────────────────
        defaults = [
            ('situation','On'), ('share','false'),
            ('start_text','❄️ Anime Botga xush kelibsiz!'),
            ('help_text','Yordam uchun admin bilan bogʻlaning.'),
            ('ads_text','Reklama matni'),
            ('anime_channel','@KinoLiveUz'),
            ('referral_bonus','100'),
            ('anthropic_api_key',''),
            ('ab_test_active','true'),
            ('premium_price','5000'),
        ]
        c.executemany('INSERT OR IGNORE INTO bot_settings (key,value) VALUES (?,?)', defaults)
        conn.commit()
        conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # USERS
    # ══════════════════════════════════════════════════════════════════════
    def add_user(self, user_id, username, first_name, last_name, referral_by=None):
        import random
        ab_group = 'A' if random.random() < 0.5 else 'B'
        conn = self.get_connection()
        conn.execute(
            '''INSERT OR IGNORE INTO users
               (user_id,username,first_name,last_name,referral_by,ab_group)
               VALUES (?,?,?,?,?,?)''',
            (user_id, username, first_name, last_name, referral_by, ab_group))
        conn.commit(); conn.close()

    def get_user(self, user_id):
        conn = self.get_connection()
        row = conn.execute('SELECT * FROM users WHERE user_id=?',(user_id,)).fetchone()
        conn.close(); return dict(row) if row else None

    def is_new_user(self, user_id):
        conn = self.get_connection()
        row = conn.execute('SELECT user_id FROM users WHERE user_id=?',(user_id,)).fetchone()
        conn.close(); return row is None

    def update_user_balance(self, user_id, amount):
        conn = self.get_connection()
        conn.execute('UPDATE users SET balance=balance+? WHERE user_id=?',(amount,user_id))
        conn.commit(); conn.close()

    def set_user_vip(self, user_id, vip_time):
        conn = self.get_connection()
        conn.execute('UPDATE users SET status="Premium +",vip_time=? WHERE user_id=?',(vip_time,user_id))
        conn.commit(); conn.close()

    def set_user_language(self, user_id, lang):
        conn = self.get_connection()
        conn.execute('UPDATE users SET language=? WHERE user_id=?',(lang,user_id))
        conn.commit(); conn.close()

    def update_last_seen(self, user_id):
        now = datetime.now().strftime('%Y-%m-%d')
        conn = self.get_connection()
        row = conn.execute('SELECT last_seen, streak FROM users WHERE user_id=?',(user_id,)).fetchone()
        if row:
            last = row['last_seen']; streak = row['streak'] or 0
            today = now
            if last == today:
                pass
            elif last and (datetime.strptime(today,'%Y-%m-%d') - datetime.strptime(last,'%Y-%m-%d')).days == 1:
                streak += 1
                conn.execute('UPDATE users SET streak=?,last_seen=? WHERE user_id=?',(streak,today,user_id))
            else:
                conn.execute('UPDATE users SET streak=1,last_seen=? WHERE user_id=?',(today,user_id))
        conn.commit(); conn.close()

    def add_coins(self, user_id, amount, reason=''):
        conn = self.get_connection()
        conn.execute('UPDATE users SET coins=coins+? WHERE user_id=?',(amount,user_id))
        conn.execute('INSERT INTO coin_transactions (user_id,amount,reason) VALUES (?,?,?)',(user_id,amount,reason))
        conn.commit(); conn.close()

    def get_all_users(self):
        conn = self.get_connection()
        rows = conn.execute('SELECT user_id FROM users').fetchall()
        conn.close(); return [r[0] for r in rows]

    def get_user_count(self):
        conn = self.get_connection()
        c = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        conn.close(); return c

    def get_today_users(self):
        today = datetime.now().strftime('%Y-%m-%d')
        conn = self.get_connection()
        c = conn.execute("SELECT COUNT(*) FROM users WHERE created_at LIKE ?",(f'{today}%',)).fetchone()[0]
        conn.close(); return c

    def get_referral_count(self, user_id):
        conn = self.get_connection()
        c = conn.execute('SELECT COUNT(*) FROM users WHERE referral_by=?',(user_id,)).fetchone()[0]
        conn.close(); return c

    # ══════════════════════════════════════════════════════════════════════
    # ANIME
    # ══════════════════════════════════════════════════════════════════════
    def add_anime(self, name, episode, country, language, image, description, genre, is_vip=0, early_access=0):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute(
            '''INSERT INTO anime (name,episode,country,language,image,description,genre,is_vip,early_access)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (name,episode,country,language,image,description,genre,is_vip,early_access))
        aid = cur.lastrowid; conn.commit(); conn.close(); return aid

    def update_anime(self, anime_id, field, value):
        conn = self.get_connection()
        conn.execute(f'UPDATE anime SET {field}=? WHERE id=?',(value,anime_id))
        conn.commit(); conn.close()

    def delete_anime(self, anime_id):
        conn = self.get_connection()
        for tbl,col in [('anime_episodes','anime_id'),('anime_ratings','anime_id'),
                        ('watch_progress','anime_id'),('watchlist','anime_id'),
                        ('anime_clips','anime_id')]:
            conn.execute(f'DELETE FROM {tbl} WHERE {col}=?',(anime_id,))
        conn.execute('DELETE FROM anime WHERE id=?',(anime_id,))
        conn.commit(); conn.close()

    def get_all_anime(self):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime ORDER BY id DESC').fetchall()
        conn.close(); return [dict(r) for r in rows]

    def search_anime_by_name(self, name):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime WHERE name LIKE ? LIMIT 10',(f'%{name}%',)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def search_anime_by_id(self, anime_id):
        conn = self.get_connection()
        row = conn.execute('SELECT * FROM anime WHERE id=?',(anime_id,)).fetchone()
        conn.close(); return dict(row) if row else None

    def search_anime_by_genre(self, genre):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime WHERE genre LIKE ? LIMIT 10',(f'%{genre}%',)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def get_top_anime(self, limit=10):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime ORDER BY rating DESC,views DESC LIMIT ?',(limit,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def increment_views(self, anime_id):
        conn = self.get_connection()
        conn.execute('UPDATE anime SET views=views+1 WHERE id=?',(anime_id,))
        conn.commit(); conn.close()

    def get_new_releases(self, limit=5):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime ORDER BY id DESC LIMIT ?',(limit,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def get_early_access_anime(self):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime WHERE early_access=1 ORDER BY id DESC').fetchall()
        conn.close(); return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════════════════
    # AI RECOMMENDATION ENGINE 2.0
    # ══════════════════════════════════════════════════════════════════════
    def get_smart_recommendations(self, user_id, limit=5):
        """
        History + rating + janr asosida smart recommendation.
        Score = rating_score * 0.5 + genre_match * 0.3 + popularity * 0.2
        """
        conn = self.get_connection()

        # Foydalanuvchi ko'rgan animelari
        watched_ids = [r[0] for r in conn.execute(
            'SELECT anime_id FROM watch_progress WHERE user_id=?',(user_id,)).fetchall()]

        # Yuqori baho bergan janrlar
        top_genres_raw = conn.execute(
            '''SELECT a.genre, AVG(r.rating) as avg_r
               FROM anime_ratings r JOIN anime a ON r.anime_id=a.id
               WHERE r.user_id=? GROUP BY a.genre ORDER BY avg_r DESC LIMIT 5''',
            (user_id,)).fetchall()
        top_genres = [row[0] for row in top_genres_raw]

        # Janr preferenslar
        genre_prefs = [r[0] for r in conn.execute(
            'SELECT genre FROM user_genres WHERE user_id=?',(user_id,)).fetchall()]

        all_genres = list(set(top_genres + genre_prefs))

        # Ko'rilmagan animelari
        if watched_ids:
            placeholders = ','.join('?' * len(watched_ids))
            candidates = conn.execute(
                f'SELECT * FROM anime WHERE id NOT IN ({placeholders}) ORDER BY rating DESC, views DESC LIMIT 50',
                watched_ids).fetchall()
        else:
            candidates = conn.execute(
                'SELECT * FROM anime ORDER BY rating DESC, views DESC LIMIT 50').fetchall()

        conn.close()
        candidates = [dict(r) for r in candidates]

        if not candidates:
            return []

        # Scoring
        scored = []
        max_views = max((a['views'] for a in candidates), default=1) or 1

        for anime in candidates:
            genre_score = 0
            anime_genres = (anime['genre'] or '').split(',')
            for ag in anime_genres:
                ag = ag.strip()
                for ug in all_genres:
                    if ug.lower() in ag.lower() or ag.lower() in ug.lower():
                        genre_score += 1

            rating_score    = (anime['rating'] or 0) / 10
            popularity_score = (anime['views'] or 0) / max_views
            genre_norm      = min(genre_score / max(len(all_genres), 1), 1.0)

            total = rating_score * 0.5 + genre_norm * 0.3 + popularity_score * 0.2
            scored.append((total, anime))

        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for score, anime in scored[:limit]:
            anime['match_percent'] = min(int(score * 100) + 40, 99)
            result.append(anime)
        return result

    def get_for_you_feed(self, user_id, offset=0, limit=1):
        """TikTok style - bittadan chiqaradi"""
        recs = self.get_smart_recommendations(user_id, limit=20)
        if offset < len(recs):
            return recs[offset:offset+limit]
        # Tugab qolsa top animelerdan
        conn = self.get_connection()
        rows = conn.execute(
            'SELECT * FROM anime ORDER BY rating DESC, views DESC LIMIT ? OFFSET ?',
            (limit, offset)).fetchall()
        conn.close()
        result = [dict(r) for r in rows]
        for a in result:
            a['match_percent'] = None
        return result

    # ══════════════════════════════════════════════════════════════════════
    # ANIME DNA PROFILE
    # ══════════════════════════════════════════════════════════════════════
    def get_anime_dna(self, user_id):
        """Foydalanuvchi ko'rgan anime janrlari asosida DNA profil"""
        conn = self.get_connection()
        # Ko'rgan va baho bergan animelari
        rows = conn.execute(
            '''SELECT a.genre, COALESCE(r.rating, 5) as w
               FROM watch_progress wp
               JOIN anime a ON wp.anime_id = a.id
               LEFT JOIN anime_ratings r ON r.anime_id=a.id AND r.user_id=wp.user_id
               WHERE wp.user_id=?''', (user_id,)).fetchall()
        conn.close()

        DNA_CATEGORIES = {
            'Action':      ['Action','Fight','Battle','War','Martial'],
            'Romance':     ['Romance','Love','Shoujo','Drama','Slice of Life'],
            'Dark':        ['Dark','Horror','Thriller','Mystery','Psychological','Death'],
            'Comedy':      ['Comedy','Gag','Parody','School','Slice'],
            'Fantasy':     ['Fantasy','Magic','Isekai','Adventure','Supernatural'],
            'Sci-Fi':      ['Sci-Fi','Mecha','Cyberpunk','Space','Futuristic'],
        }

        counts = {k: 0.0 for k in DNA_CATEGORIES}
        total_weight = 0.0

        for row in rows:
            genre_str = row['genre'] or ''
            weight = row['w'] / 10.0
            total_weight += weight
            for dna_key, keywords in DNA_CATEGORIES.items():
                for kw in keywords:
                    if kw.lower() in genre_str.lower():
                        counts[dna_key] += weight
                        break

        if total_weight == 0:
            return None  # Hali hech narsa ko'rmagan

        result = {}
        for k, v in counts.items():
            result[k] = min(int((v / total_weight) * 100), 99)

        # Normalize to ~100%
        total = sum(result.values())
        if total > 0:
            for k in result:
                result[k] = int(result[k] * 100 / total)

        return result

    # ══════════════════════════════════════════════════════════════════════
    # DAILY MISSIONS & GAMIFICATION
    # ══════════════════════════════════════════════════════════════════════
    MISSIONS = {
        'watch_episode': {'target': 2, 'reward': 10,  'text': '🎬 2 ta qism ko\'r',       'icon': '🎬'},
        'give_rating':   {'target': 1, 'reward': 5,   'text': '⭐ 1 ta baho ber',          'icon': '⭐'},
        'daily_login':   {'target': 1, 'reward': 3,   'text': '📅 Bugun kirish',            'icon': '📅'},
        'search_anime':  {'target': 1, 'reward': 2,   'text': '🔎 1 ta anime qidir',        'icon': '🔎'},
        'add_watchlist': {'target': 1, 'reward': 5,   'text': '🔔 Kuzatuvga qo\'sh',        'icon': '🔔'},
    }

    def get_daily_missions(self, user_id):
        today = date.today().isoformat()
        conn = self.get_connection()
        result = []
        for key, info in self.MISSIONS.items():
            row = conn.execute(
                'SELECT * FROM daily_missions WHERE user_id=? AND mission_key=? AND date=?',
                (user_id, key, today)).fetchone()
            if row:
                m = dict(row)
            else:
                m = {'mission_key': key, 'progress': 0, 'completed': 0}
            m.update(info)
            result.append(m)
        conn.close()
        return result

    def update_mission(self, user_id, mission_key, increment=1):
        """Mission progressini oshiradi, completed bo'lsa coin beradi"""
        today = date.today().isoformat()
        info = self.MISSIONS.get(mission_key)
        if not info:
            return False, 0

        conn = self.get_connection()
        row = conn.execute(
            'SELECT * FROM daily_missions WHERE user_id=? AND mission_key=? AND date=?',
            (user_id, mission_key, today)).fetchone()

        if row and row['completed']:
            conn.close(); return False, 0

        if row:
            new_progress = row['progress'] + increment
            completed = 1 if new_progress >= info['target'] else 0
            conn.execute(
                'UPDATE daily_missions SET progress=?,completed=? WHERE user_id=? AND mission_key=? AND date=?',
                (new_progress, completed, user_id, mission_key, today))
        else:
            new_progress = increment
            completed = 1 if new_progress >= info['target'] else 0
            conn.execute(
                'INSERT INTO daily_missions (user_id,mission_key,progress,completed,date) VALUES (?,?,?,?,?)',
                (user_id, mission_key, new_progress, completed, today))

        conn.commit(); conn.close()

        if completed:
            self.add_coins(user_id, info['reward'], f"Mission: {mission_key}")
            return True, info['reward']
        return False, 0

    def get_streak_bonus(self, streak):
        if streak >= 30: return 50
        if streak >= 14: return 30
        if streak >= 7:  return 20
        if streak >= 3:  return 10
        return 0

    def get_leaderboard(self, limit=10):
        conn = self.get_connection()
        rows = conn.execute(
            'SELECT user_id,first_name,coins,streak FROM users ORDER BY coins DESC LIMIT ?',
            (limit,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════════════════
    # CLIPS (SHORTS)
    # ══════════════════════════════════════════════════════════════════════
    def add_clip(self, anime_id, file_id, caption=''):
        conn = self.get_connection()
        conn.execute('INSERT INTO anime_clips (anime_id,file_id,caption) VALUES (?,?,?)',
                     (anime_id, file_id, caption))
        conn.commit(); conn.close()

    def get_clips(self, anime_id):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime_clips WHERE anime_id=? ORDER BY id',(anime_id,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def get_random_clips(self, limit=5):
        conn = self.get_connection()
        rows = conn.execute(
            '''SELECT c.*,a.name,a.genre FROM anime_clips c
               JOIN anime a ON c.anime_id=a.id
               ORDER BY RANDOM() LIMIT ?''',(limit,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def delete_clip(self, clip_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM anime_clips WHERE id=?',(clip_id,))
        conn.commit(); conn.close()

    def increment_clip_views(self, clip_id):
        conn = self.get_connection()
        conn.execute('UPDATE anime_clips SET views=views+1 WHERE id=?',(clip_id,))
        conn.commit(); conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # AI CHAT HISTORY
    # ══════════════════════════════════════════════════════════════════════
    def add_ai_message(self, user_id, role, content):
        conn = self.get_connection()
        conn.execute('INSERT INTO ai_chat_history (user_id,role,content) VALUES (?,?,?)',
                     (user_id, role, content))
        conn.commit(); conn.close()

    def get_ai_history(self, user_id, limit=10):
        conn = self.get_connection()
        rows = conn.execute(
            '''SELECT role,content FROM ai_chat_history
               WHERE user_id=? ORDER BY id DESC LIMIT ?''',(user_id, limit)).fetchall()
        conn.close()
        return list(reversed([dict(r) for r in rows]))

    def clear_ai_history(self, user_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM ai_chat_history WHERE user_id=?',(user_id,))
        conn.commit(); conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # A/B TESTING
    # ══════════════════════════════════════════════════════════════════════
    def get_ab_group(self, user_id):
        conn = self.get_connection()
        row = conn.execute('SELECT ab_group FROM users WHERE user_id=?',(user_id,)).fetchone()
        conn.close(); return row['ab_group'] if row else 'A'

    def log_ab_event(self, user_id, event):
        ab_group = self.get_ab_group(user_id)
        conn = self.get_connection()
        conn.execute('INSERT INTO ab_events (user_id,ab_group,event) VALUES (?,?,?)',
                     (user_id, ab_group, event))
        conn.commit(); conn.close()

    def get_ab_stats(self):
        conn = self.get_connection()
        stats = {}
        for group in ('A','B'):
            total = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM users WHERE ab_group=?",(group,)).fetchone()[0]
            events = conn.execute(
                "SELECT event, COUNT(*) as cnt FROM ab_events WHERE ab_group=? GROUP BY event",(group,)).fetchall()
            stats[group] = {'total_users': total, 'events': {r['event']:r['cnt'] for r in events}}
        conn.close(); return stats

    # ══════════════════════════════════════════════════════════════════════
    # EPISODES
    # ══════════════════════════════════════════════════════════════════════
    def add_episode(self, anime_id, episode_number, file_id):
        conn = self.get_connection()
        conn.execute('INSERT INTO anime_episodes (anime_id,episode_number,file_id) VALUES (?,?,?)',
                     (anime_id, episode_number, file_id))
        conn.commit(); conn.close()

    def get_episode_by_id(self, episode_id):
        conn = self.get_connection()
        row = conn.execute('SELECT * FROM anime_episodes WHERE id=?',(episode_id,)).fetchone()
        conn.close(); return dict(row) if row else None

    def get_anime_episodes(self, anime_id):
        conn = self.get_connection()
        rows = conn.execute(
            'SELECT * FROM anime_episodes WHERE anime_id=? ORDER BY episode_number',(anime_id,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def update_episode(self, episode_id, file_id):
        conn = self.get_connection()
        conn.execute('UPDATE anime_episodes SET file_id=? WHERE id=?',(file_id,episode_id))
        conn.commit(); conn.close()

    def delete_episode(self, episode_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM anime_episodes WHERE id=?',(episode_id,))
        conn.commit(); conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # RATINGS
    # ══════════════════════════════════════════════════════════════════════
    def add_rating(self, anime_id, user_id, rating, review=None):
        conn = self.get_connection()
        conn.execute('INSERT OR REPLACE INTO anime_ratings (anime_id,user_id,rating,review) VALUES (?,?,?,?)',
                     (anime_id, user_id, rating, review))
        conn.commit()
        avg = conn.execute('SELECT AVG(rating) FROM anime_ratings WHERE anime_id=?',(anime_id,)).fetchone()[0]
        conn.execute('UPDATE anime SET rating=? WHERE id=?',(round(avg,1),anime_id))
        conn.commit(); conn.close()

    def get_user_rating(self, anime_id, user_id):
        conn = self.get_connection()
        row = conn.execute('SELECT * FROM anime_ratings WHERE anime_id=? AND user_id=?',(anime_id,user_id)).fetchone()
        conn.close(); return dict(row) if row else None

    def get_anime_reviews(self, anime_id, limit=5):
        conn = self.get_connection()
        rows = conn.execute(
            '''SELECT r.*,u.first_name FROM anime_ratings r
               JOIN users u ON r.user_id=u.user_id
               WHERE r.anime_id=? AND r.review IS NOT NULL
               ORDER BY r.created_at DESC LIMIT ?''',(anime_id,limit)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════════════════
    # WATCH PROGRESS
    # ══════════════════════════════════════════════════════════════════════
    def save_progress(self, user_id, anime_id, episode_number):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = self.get_connection()
        conn.execute(
            '''INSERT INTO watch_progress (user_id,anime_id,episode_number,updated_at)
               VALUES (?,?,?,?)
               ON CONFLICT(user_id,anime_id) DO UPDATE SET episode_number=?,updated_at=?''',
            (user_id,anime_id,episode_number,now,episode_number,now))
        conn.commit(); conn.close()

    def get_progress(self, user_id, anime_id):
        conn = self.get_connection()
        row = conn.execute('SELECT * FROM watch_progress WHERE user_id=? AND anime_id=?',(user_id,anime_id)).fetchone()
        conn.close(); return dict(row) if row else None

    def get_user_history(self, user_id, limit=10):
        conn = self.get_connection()
        rows = conn.execute(
            '''SELECT wp.*,a.name,a.episode,a.image FROM watch_progress wp
               JOIN anime a ON wp.anime_id=a.id
               WHERE wp.user_id=? ORDER BY wp.updated_at DESC LIMIT ?''',(user_id,limit)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════════════════
    # WATCHLIST
    # ══════════════════════════════════════════════════════════════════════
    def add_to_watchlist(self, user_id, anime_id):
        conn = self.get_connection()
        try:
            conn.execute('INSERT INTO watchlist (user_id,anime_id) VALUES (?,?)',(user_id,anime_id))
            conn.commit(); conn.close(); return True
        except sqlite3.IntegrityError:
            conn.close(); return False

    def remove_from_watchlist(self, user_id, anime_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM watchlist WHERE user_id=? AND anime_id=?',(user_id,anime_id))
        conn.commit(); conn.close()

    def is_in_watchlist(self, user_id, anime_id):
        conn = self.get_connection()
        row = conn.execute('SELECT id FROM watchlist WHERE user_id=? AND anime_id=?',(user_id,anime_id)).fetchone()
        conn.close(); return row is not None

    def get_watchlist_subscribers(self, anime_id):
        conn = self.get_connection()
        rows = conn.execute('SELECT user_id FROM watchlist WHERE anime_id=?',(anime_id,)).fetchall()
        conn.close(); return [r[0] for r in rows]

    def get_user_watchlist(self, user_id):
        conn = self.get_connection()
        rows = conn.execute(
            '''SELECT w.*,a.name,a.episode,a.image,a.genre FROM watchlist w
               JOIN anime a ON w.anime_id=a.id
               WHERE w.user_id=? ORDER BY w.created_at DESC''',(user_id,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════════════════
    # SCHEDULED POSTS
    # ══════════════════════════════════════════════════════════════════════
    def add_scheduled_post(self, anime_id, channel, scheduled_at):
        conn = self.get_connection()
        conn.execute('INSERT INTO scheduled_posts (anime_id,channel,scheduled_at) VALUES (?,?,?)',
                     (anime_id, channel, scheduled_at))
        conn.commit(); conn.close()

    def get_pending_posts(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        conn = self.get_connection()
        rows = conn.execute(
            '''SELECT sp.*,a.name,a.image,a.episode,a.country,a.language,
                      a.genre,a.rating,a.description
               FROM scheduled_posts sp JOIN anime a ON sp.anime_id=a.id
               WHERE sp.scheduled_at<=? AND sp.sent=0''',(now,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def mark_post_sent(self, post_id):
        conn = self.get_connection()
        conn.execute('UPDATE scheduled_posts SET sent=1 WHERE id=?',(post_id,))
        conn.commit(); conn.close()

    def get_all_scheduled_posts(self):
        conn = self.get_connection()
        rows = conn.execute(
            '''SELECT sp.*,a.name FROM scheduled_posts sp
               JOIN anime a ON sp.anime_id=a.id
               WHERE sp.sent=0 ORDER BY sp.scheduled_at ASC''').fetchall()
        conn.close(); return [dict(r) for r in rows]

    def delete_scheduled_post(self, post_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM scheduled_posts WHERE id=?',(post_id,))
        conn.commit(); conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # GENRE PREFERENCES
    # ══════════════════════════════════════════════════════════════════════
    def save_user_genres(self, user_id, genres: list):
        conn = self.get_connection()
        conn.execute('DELETE FROM user_genres WHERE user_id=?',(user_id,))
        for genre in genres:
            try:
                conn.execute('INSERT INTO user_genres (user_id,genre) VALUES (?,?)',(user_id,genre))
            except sqlite3.IntegrityError: pass
        conn.commit(); conn.close()

    def get_user_genres(self, user_id):
        conn = self.get_connection()
        rows = conn.execute('SELECT genre FROM user_genres WHERE user_id=?',(user_id,)).fetchall()
        conn.close(); return [r[0] for r in rows]

    def has_genre_preferences(self, user_id):
        conn = self.get_connection()
        row = conn.execute('SELECT id FROM user_genres WHERE user_id=?',(user_id,)).fetchone()
        conn.close(); return row is not None

    # ══════════════════════════════════════════════════════════════════════
    # CHANNELS
    # ══════════════════════════════════════════════════════════════════════
    def add_channel(self, channel_id, channel_link, channel_type='request'):
        conn = self.get_connection()
        conn.execute('INSERT OR REPLACE INTO channels (channel_id,channel_link,channel_type) VALUES (?,?,?)',
                     (channel_id, channel_link, channel_type))
        conn.commit(); conn.close()

    def get_channels(self, channel_type='request'):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM channels WHERE channel_type=?',(channel_type,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def delete_channel(self, channel_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM channels WHERE channel_id=?',(channel_id,))
        conn.commit(); conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # PAYMENTS
    # ══════════════════════════════════════════════════════════════════════
    def add_payment(self, user_id, amount, photo):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('INSERT INTO payments (user_id,amount,photo) VALUES (?,?,?)',(user_id,amount,photo))
        pid = cur.lastrowid; conn.commit(); conn.close(); return pid

    def update_payment_status(self, payment_id, status):
        conn = self.get_connection()
        conn.execute('UPDATE payments SET status=? WHERE id=?',(status,payment_id))
        conn.commit(); conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # SETTINGS
    # ══════════════════════════════════════════════════════════════════════
    def get_setting(self, key):
        conn = self.get_connection()
        row = conn.execute('SELECT value FROM bot_settings WHERE key=?',(key,)).fetchone()
        conn.close(); return row[0] if row else None

    def update_setting(self, key, value):
        conn = self.get_connection()
        conn.execute('INSERT OR REPLACE INTO bot_settings (key,value) VALUES (?,?)',(key,value))
        conn.commit(); conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # STATS
    # ══════════════════════════════════════════════════════════════════════
    def get_most_viewed_anime(self, limit=5):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM anime ORDER BY views DESC LIMIT ?',(limit,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def get_stats(self):
        conn = self.get_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        s = {
            'total_users':    conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
            'today_users':    conn.execute("SELECT COUNT(*) FROM users WHERE created_at LIKE ?",(f'{today}%',)).fetchone()[0],
            'total_anime':    conn.execute('SELECT COUNT(*) FROM anime').fetchone()[0],
            'total_episodes': conn.execute('SELECT COUNT(*) FROM anime_episodes').fetchone()[0],
            'premium_users':  conn.execute("SELECT COUNT(*) FROM users WHERE status='Premium +'"  ).fetchone()[0],
            'total_views':    conn.execute('SELECT SUM(views) FROM anime').fetchone()[0] or 0,
            'total_clips':    conn.execute('SELECT COUNT(*) FROM anime_clips').fetchone()[0],
        }
        conn.close(); return s