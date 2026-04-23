import sqlite3
from datetime import datetime, date


class Database:
    def __init__(self, db_name='anime_bot.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        # Concurrency + perf (SQLite tuning)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA temp_store=MEMORY;")
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

        # ── Social: follows ────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS user_follows (
            follower_id  INTEGER NOT NULL,
            following_id INTEGER NOT NULL,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (follower_id, following_id),
            FOREIGN KEY (follower_id)  REFERENCES users (user_id),
            FOREIGN KEY (following_id) REFERENCES users (user_id)
        )''')

        # ── Activity feed events ───────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS activity_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            anime_id    INTEGER,
            episode_number INTEGER,
            event_type  TEXT NOT NULL, -- started_anime | finished_episode
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        # ── Live activity: "who is watching now" (fake realtime) ───────────
        c.execute('''CREATE TABLE IF NOT EXISTS watch_sessions (
            user_id    INTEGER NOT NULL,
            anime_id   INTEGER NOT NULL,
            last_ping  TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, anime_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        # ── Shorts (TikTok-style) ──────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS shorts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id   INTEGER,
            file_id    TEXT NOT NULL,
            views      INTEGER DEFAULT 0,
            likes      INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')
        c.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_shorts_file_id ON shorts(file_id)''')

        c.execute('''CREATE TABLE IF NOT EXISTS short_seen (
            user_id   INTEGER NOT NULL,
            short_id  INTEGER NOT NULL,
            seen_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, short_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (short_id) REFERENCES shorts (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS short_engagement (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            short_id   INTEGER NOT NULL,
            watch_time REAL DEFAULT 0,
            skipped    INTEGER DEFAULT 0,
            rewatched  INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (short_id) REFERENCES shorts (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS short_likes (
            user_id   INTEGER NOT NULL,
            short_id  INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, short_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (short_id) REFERENCES shorts (id)
        )''')

        # ── Comments (anime threads) ───────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id   INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            parent_id  INTEGER DEFAULT NULL,
            text       TEXT NOT NULL,
            likes      INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_id) REFERENCES anime (id),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (parent_id) REFERENCES comments (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS comment_likes (
            user_id    INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, comment_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (comment_id) REFERENCES comments (id)
        )''')

        # ── Indexes (critical for 1M-ish behavior on SQLite) ───────────────
        c.execute('CREATE INDEX IF NOT EXISTS idx_watch_progress_user_updated ON watch_progress(user_id, updated_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_anime_views_rating ON anime(views DESC, rating DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_following ON user_follows(follower_id, created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_followers ON user_follows(following_id, created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_activity_user_time ON activity_events(user_id, created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_activity_anime_time ON activity_events(anime_id, created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_watch_sessions_anime_ping ON watch_sessions(anime_id, last_ping DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_comments_anime_time ON comments(anime_id, created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id, created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_short_seen_user_time ON short_seen(user_id, seen_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_short_engagement_short_time ON short_engagement(short_id, created_at DESC)')

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

    # ══════════════════════════════════════════════════════════════════════
    # SOCIAL: FOLLOW / UNFOLLOW + PROFILE + FEED
    # ══════════════════════════════════════════════════════════════════════
    def follow_user(self, follower_id: int, following_id: int) -> bool:
        if follower_id == following_id:
            return False
        conn = self.get_connection()
        try:
            conn.execute(
                'INSERT OR IGNORE INTO user_follows (follower_id, following_id) VALUES (?,?)',
                (follower_id, following_id),
            )
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        conn = self.get_connection()
        try:
            conn.execute(
                'DELETE FROM user_follows WHERE follower_id=? AND following_id=?',
                (follower_id, following_id),
            )
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def is_following(self, follower_id: int, following_id: int) -> bool:
        conn = self.get_connection()
        row = conn.execute(
            'SELECT 1 FROM user_follows WHERE follower_id=? AND following_id=?',
            (follower_id, following_id),
        ).fetchone()
        conn.close()
        return row is not None

    def get_follow_counts(self, user_id: int) -> dict:
        conn = self.get_connection()
        following = conn.execute(
            'SELECT COUNT(*) FROM user_follows WHERE follower_id=?', (user_id,)
        ).fetchone()[0]
        followers = conn.execute(
            'SELECT COUNT(*) FROM user_follows WHERE following_id=?', (user_id,)
        ).fetchone()[0]
        conn.close()
        return {"followers": followers, "following": following}

    def get_public_profile(self, user_id: int) -> dict | None:
        conn = self.get_connection()
        user = conn.execute(
            'SELECT user_id, username, first_name, last_name, status, coins, streak FROM users WHERE user_id=?',
            (user_id,),
        ).fetchone()
        if not user:
            conn.close()
            return None

        last = conn.execute(
            '''SELECT wp.anime_id, wp.episode_number, wp.updated_at, a.name, a.image, a.genre, a.episode
               FROM watch_progress wp
               JOIN anime a ON a.id = wp.anime_id
               WHERE wp.user_id=?
               ORDER BY wp.updated_at DESC
               LIMIT 1''',
            (user_id,),
        ).fetchone()

        counts = self.get_follow_counts(user_id)
        conn.close()

        profile = dict(user)
        profile.update(counts)
        profile["last_watched"] = dict(last) if last else None
        return profile

    def log_activity(self, user_id: int, event_type: str, anime_id: int | None = None, episode_number: int | None = None):
        conn = self.get_connection()
        conn.execute(
            'INSERT INTO activity_events (user_id, anime_id, episode_number, event_type) VALUES (?,?,?,?)',
            (user_id, anime_id, episode_number, event_type),
        )
        conn.commit()
        conn.close()

    def get_activity_feed(self, user_id: int, limit: int = 30) -> list:
        """
        Foydalanuvchi follow qilgan userlar + o'zi activity feed.
        """
        conn = self.get_connection()
        rows = conn.execute(
            '''
            SELECT e.*, u.first_name, u.username, a.name AS anime_name, a.image AS anime_image
            FROM activity_events e
            JOIN users u ON u.user_id = e.user_id
            LEFT JOIN anime a ON a.id = e.anime_id
            WHERE e.user_id = ?
               OR e.user_id IN (
                  SELECT following_id FROM user_follows WHERE follower_id = ?
               )
            ORDER BY e.created_at DESC, e.id DESC
            LIMIT ?
            ''',
            (user_id, user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════════════════
    # LIVE ACTIVITY (fake realtime)
    # ══════════════════════════════════════════════════════════════════════
    def ping_watch_session(self, user_id: int, anime_id: int):
        conn = self.get_connection()
        conn.execute(
            '''INSERT INTO watch_sessions (user_id, anime_id, last_ping)
               VALUES (?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(user_id,anime_id) DO UPDATE SET last_ping=CURRENT_TIMESTAMP''',
            (user_id, anime_id),
        )
        conn.commit()
        conn.close()

    def get_active_viewers(self, anime_id: int, minutes: int = 10) -> int:
        conn = self.get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM watch_sessions WHERE anime_id=? AND last_ping >= datetime('now', ?)",
            (anime_id, f"-{minutes} minutes"),
        ).fetchone()
        conn.close()
        return int(row[0] if row else 0)

    # ══════════════════════════════════════════════════════════════════════
    # SHORTS (TikTok-style)
    # ══════════════════════════════════════════════════════════════════════
    def add_short(self, anime_id: int | None, file_id: str) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO shorts (anime_id, file_id) VALUES (?,?)', (anime_id, file_id))
        conn.commit()
        if cur.lastrowid:
            sid = cur.lastrowid
        else:
            sid = conn.execute('SELECT id FROM shorts WHERE file_id=?', (file_id,)).fetchone()[0]
        conn.close()
        return sid

    def like_short(self, user_id: int, short_id: int) -> bool:
        conn = self.get_connection()
        try:
            conn.execute('INSERT OR IGNORE INTO short_likes (user_id, short_id) VALUES (?,?)', (user_id, short_id))
            if conn.total_changes:
                conn.execute('UPDATE shorts SET likes=likes+1 WHERE id=?', (short_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def unlike_short(self, user_id: int, short_id: int) -> bool:
        conn = self.get_connection()
        try:
            conn.execute('DELETE FROM short_likes WHERE user_id=? AND short_id=?', (user_id, short_id))
            if conn.total_changes:
                conn.execute('UPDATE shorts SET likes=MAX(likes-1,0) WHERE id=?', (short_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def track_short_engagement(self, user_id: int, short_id: int, watch_time: float = 0, skipped: int = 0, rewatched: int = 0):
        conn = self.get_connection()
        conn.execute(
            'INSERT INTO short_engagement (user_id, short_id, watch_time, skipped, rewatched) VALUES (?,?,?,?,?)',
            (user_id, short_id, float(watch_time or 0), int(skipped or 0), int(rewatched or 0)),
        )
        conn.execute(
            'INSERT OR REPLACE INTO short_seen (user_id, short_id, seen_at) VALUES (?,?,CURRENT_TIMESTAMP)',
            (user_id, short_id),
        )
        conn.commit()
        conn.close()

    def increment_short_view(self, short_id: int):
        conn = self.get_connection()
        conn.execute('UPDATE shorts SET views=views+1 WHERE id=?', (short_id,))
        conn.commit()
        conn.close()

    def get_next_short(self, user_id: int) -> dict | None:
        """
        Infinite scroll: rank shorts, prefer unseen recently.
        Ranking: completion_rate + engagement_score; approximated from engagement events.
        """
        conn = self.get_connection()
        row = conn.execute(
            '''
            WITH seen AS (
              SELECT short_id FROM short_seen WHERE user_id=? AND seen_at >= datetime('now', '-7 days')
            ),
            agg AS (
              SELECT
                s.id,
                s.anime_id,
                s.file_id,
                s.views,
                s.likes,
                COALESCE(SUM(e.watch_time), 0) AS wt,
                COALESCE(SUM(e.skipped), 0) AS skips,
                COALESCE(SUM(e.rewatched), 0) AS rewatches,
                COUNT(e.id) AS events
              FROM shorts s
              LEFT JOIN short_engagement e ON e.short_id = s.id AND e.created_at >= datetime('now', '-30 days')
              GROUP BY s.id
            )
            SELECT a.*,
                   (CASE WHEN a.events>0 THEN (1.0 - (a.skips * 1.0 / a.events)) ELSE 0.5 END) AS completion_rate,
                   (a.likes * 2.0 + a.rewatches * 1.5 + a.wt * 0.05) AS engagement_score
            FROM agg a
            WHERE a.id NOT IN (SELECT short_id FROM seen)
            ORDER BY (completion_rate * 0.7 + engagement_score * 0.3) DESC, a.views DESC
            LIMIT 1
            ''',
            (user_id,),
        ).fetchone()

        if not row:
            # fallback: allow repeats
            row = conn.execute(
                'SELECT * FROM shorts ORDER BY (likes*3 + views) DESC, id DESC LIMIT 1'
            ).fetchone()
        conn.close()
        return dict(row) if row else None

    # ══════════════════════════════════════════════════════════════════════
    # COMMENTS
    # ══════════════════════════════════════════════════════════════════════
    def add_comment(self, anime_id: int, user_id: int, text: str, parent_id: int | None = None) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO comments (anime_id, user_id, parent_id, text) VALUES (?,?,?,?)',
            (anime_id, user_id, parent_id, text),
        )
        cid = cur.lastrowid
        conn.commit()
        conn.close()
        return cid

    def like_comment(self, user_id: int, comment_id: int) -> bool:
        conn = self.get_connection()
        try:
            conn.execute('INSERT OR IGNORE INTO comment_likes (user_id, comment_id) VALUES (?,?)', (user_id, comment_id))
            if conn.total_changes:
                conn.execute('UPDATE comments SET likes=likes+1 WHERE id=?', (comment_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def get_comments(self, anime_id: int, limit: int = 50) -> list:
        """
        Returns top-level comments with 0-2 replies (prefetched).
        Ranking: likes desc, created_at desc
        """
        conn = self.get_connection()
        top = conn.execute(
            '''
            SELECT c.*, u.first_name, u.username
            FROM comments c
            JOIN users u ON u.user_id=c.user_id
            WHERE c.anime_id=? AND c.parent_id IS NULL
            ORDER BY c.likes DESC, c.created_at DESC, c.id DESC
            LIMIT ?
            ''',
            (anime_id, limit),
        ).fetchall()

        top_ids = [r["id"] for r in top]
        replies_by_parent = {}
        if top_ids:
            placeholders = ",".join("?" * len(top_ids))
            replies = conn.execute(
                f'''
                SELECT c.*, u.first_name, u.username
                FROM comments c
                JOIN users u ON u.user_id=c.user_id
                WHERE c.parent_id IN ({placeholders})
                ORDER BY c.likes DESC, c.created_at ASC, c.id ASC
                ''',
                top_ids,
            ).fetchall()
            for r in replies:
                replies_by_parent.setdefault(r["parent_id"], []).append(dict(r))
        conn.close()

        out = []
        for r in top:
            item = dict(r)
            item["replies"] = (replies_by_parent.get(item["id"], [])[:2])
            out.append(item)
        return out

    # ══════════════════════════════════════════════════════════════════════
    # RECOMMENDATIONS (requested scoring formula)
    # ══════════════════════════════════════════════════════════════════════
    def get_recommended_anime(self, user_id: int, limit: int = 10) -> list:
        """
        score = (watch_time * 0.4) + (completion_rate * 0.3) + (genre_match * 0.2) + (popularity * 0.1)

        SQLite reality check: Telegram doesn't provide real watch-time, so we approximate watch_time
        from progress (episode_number) and treat it as a relative signal. The service layer can
        later feed real watch_time if you add explicit "watched X sec" events.
        """
        conn = self.get_connection()

        # User genre preferences (explicit onboarding)
        prefs = [r[0] for r in conn.execute('SELECT genre FROM user_genres WHERE user_id=?', (user_id,)).fetchall()]
        prefs_l = [p.lower() for p in prefs]

        # Watched progress (proxy for watch_time & completion)
        progress = conn.execute(
            'SELECT anime_id, episode_number FROM watch_progress WHERE user_id=?',
            (user_id,),
        ).fetchall()
        prog_map = {r["anime_id"]: int(r["episode_number"] or 0) for r in progress}

        # Candidates (exclude nothing; rank will push watched down if completed)
        candidates = conn.execute(
            'SELECT id, name, genre, episode, rating, views, is_vip, early_access, description, image FROM anime ORDER BY views DESC, rating DESC LIMIT 300'
        ).fetchall()

        max_views = max((int(r["views"] or 0) for r in candidates), default=1) or 1

        scored = []
        for a in candidates:
            anime_id = a["id"]
            total_eps = max(int(a["episode"] or 1), 1)
            watched_eps = min(int(prog_map.get(anime_id, 0)), total_eps)

            # proxies
            watch_time = watched_eps / total_eps  # 0..1
            completion_rate = watched_eps / total_eps  # 0..1

            anime_genres = [g.strip().lower() for g in (a["genre"] or "").split(",") if g.strip()]
            if prefs_l and anime_genres:
                matches = sum(1 for g in anime_genres for p in prefs_l if p in g or g in p)
                genre_match = min(matches / max(len(prefs_l), 1), 1.0)
            elif prefs_l:
                genre_match = 0.0
            else:
                # cold start: no prefs => neutral genre match
                genre_match = 0.5

            popularity = (int(a["views"] or 0) / max_views) if max_views else 0.0

            score = (watch_time * 0.4) + (completion_rate * 0.3) + (genre_match * 0.2) + (popularity * 0.1)

            item = dict(a)
            item["score"] = round(score, 4)
            item["match_percent"] = min(max(int(score * 100), 1), 99)
            scored.append(item)

        conn.close()
        scored.sort(key=lambda x: (x["score"], x.get("views", 0)), reverse=True)
        return scored[:limit]