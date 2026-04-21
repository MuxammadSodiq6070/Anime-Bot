import sqlite3
from datetime import datetime


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

        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT, first_name TEXT, last_name TEXT,
            status      TEXT    DEFAULT 'Simple',
            balance     INTEGER DEFAULT 0,
            vip_time    TEXT    DEFAULT '00.00.0000 00:00',
            language    TEXT    DEFAULT 'uz',
            referral_by INTEGER DEFAULT NULL,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        )''')

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
            create_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS anime_episodes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id       INTEGER, episode_number INTEGER, file_id TEXT,
            created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS channels (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id   TEXT UNIQUE, channel_link TEXT,
            channel_type TEXT DEFAULT 'request'
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, amount INTEGER, photo TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY, value TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS anime_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER, user_id INTEGER,
            rating INTEGER, review TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(anime_id, user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id),
            FOREIGN KEY (user_id)  REFERENCES users (user_id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS watch_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, anime_id INTEGER,
            episode_number INTEGER DEFAULT 1,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_id),
            FOREIGN KEY (user_id)  REFERENCES users (user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, anime_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_id),
            FOREIGN KEY (user_id)  REFERENCES users (user_id),
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER, channel TEXT,
            scheduled_at TEXT, sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS user_genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, genre TEXT,
            UNIQUE(user_id, genre),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        defaults = [
            ('situation','On'),('share','false'),
            ('start_text','❄️ Anime Botga xush kelibsiz!'),
            ('help_text','Yordam uchun admin bilan bogʻlaning.'),
            ('ads_text','Reklama matni'),('anime_channel','@KinoLiveUz'),
            ('referral_bonus','100'),
        ]
        c.executemany('INSERT OR IGNORE INTO bot_settings (key,value) VALUES (?,?)', defaults)
        conn.commit()
        conn.close()

    # ── Users ──────────────────────────────────────────────────────────────
    def add_user(self, user_id, username, first_name, last_name, referral_by=None):
        conn = self.get_connection()
        conn.execute(
            'INSERT OR IGNORE INTO users (user_id,username,first_name,last_name,referral_by) VALUES (?,?,?,?,?)',
            (user_id, username, first_name, last_name, referral_by))
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

    # ── Anime ──────────────────────────────────────────────────────────────
    def add_anime(self, name, episode, country, language, image, description, genre, is_vip=0):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute(
            'INSERT INTO anime (name,episode,country,language,image,description,genre,is_vip) VALUES (?,?,?,?,?,?,?,?)',
            (name,episode,country,language,image,description,genre,is_vip))
        aid = cur.lastrowid; conn.commit(); conn.close(); return aid

    def update_anime(self, anime_id, field, value):
        conn = self.get_connection()
        conn.execute(f'UPDATE anime SET {field}=? WHERE id=?',(value,anime_id))
        conn.commit(); conn.close()

    def delete_anime(self, anime_id):
        conn = self.get_connection()
        for tbl,col in [('anime_episodes','anime_id'),('anime_ratings','anime_id'),
                        ('watch_progress','anime_id'),('watchlist','anime_id')]:
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

    def get_recommended_anime(self, user_id, limit=5):
        genres = self.get_user_genres(user_id)
        if not genres:
            return self.get_top_anime(limit)
        conn = self.get_connection()
        conditions = ' OR '.join([f"genre LIKE ?" for _ in genres])
        rows = conn.execute(
            f'SELECT * FROM anime WHERE ({conditions}) ORDER BY rating DESC,views DESC LIMIT ?',
            [f'%{g}%' for g in genres] + [limit]
        ).fetchall()
        conn.close(); return [dict(r) for r in rows]

    # ── Episodes ───────────────────────────────────────────────────────────
    def add_episode(self, anime_id, episode_number, file_id):
        conn = self.get_connection()
        conn.execute('INSERT INTO anime_episodes (anime_id,episode_number,file_id) VALUES (?,?,?)',
                     (anime_id,episode_number,file_id))
        conn.commit(); conn.close()

    def update_episode(self, episode_id, file_id):
        conn = self.get_connection()
        conn.execute('UPDATE anime_episodes SET file_id=? WHERE id=?',(file_id,episode_id))
        conn.commit(); conn.close()

    def delete_episode(self, episode_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM anime_episodes WHERE id=?',(episode_id,))
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

    # ── Ratings ────────────────────────────────────────────────────────────
    def add_rating(self, anime_id, user_id, rating, review=None):
        conn = self.get_connection()
        conn.execute(
            'INSERT OR REPLACE INTO anime_ratings (anime_id,user_id,rating,review) VALUES (?,?,?,?)',
            (anime_id,user_id,rating,review))
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

    # ── Watch progress ─────────────────────────────────────────────────────
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

    # ── Watchlist ──────────────────────────────────────────────────────────
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

    # ── Scheduled posts ────────────────────────────────────────────────────
    def add_scheduled_post(self, anime_id, channel, scheduled_at):
        conn = self.get_connection()
        conn.execute('INSERT INTO scheduled_posts (anime_id,channel,scheduled_at) VALUES (?,?,?)',
                     (anime_id,channel,scheduled_at))
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

    # ── Genre preferences ──────────────────────────────────────────────────
    def save_user_genres(self, user_id, genres: list):
        conn = self.get_connection()
        conn.execute('DELETE FROM user_genres WHERE user_id=?',(user_id,))
        for genre in genres:
            try:
                conn.execute('INSERT INTO user_genres (user_id,genre) VALUES (?,?)',(user_id,genre))
            except sqlite3.IntegrityError:
                pass
        conn.commit(); conn.close()

    def get_user_genres(self, user_id):
        conn = self.get_connection()
        rows = conn.execute('SELECT genre FROM user_genres WHERE user_id=?',(user_id,)).fetchall()
        conn.close(); return [r[0] for r in rows]

    def has_genre_preferences(self, user_id):
        conn = self.get_connection()
        row = conn.execute('SELECT id FROM user_genres WHERE user_id=?',(user_id,)).fetchone()
        conn.close(); return row is not None

    # ── Channels ───────────────────────────────────────────────────────────
    def add_channel(self, channel_id, channel_link, channel_type='request'):
        conn = self.get_connection()
        conn.execute('INSERT OR REPLACE INTO channels (channel_id,channel_link,channel_type) VALUES (?,?,?)',
                     (channel_id,channel_link,channel_type))
        conn.commit(); conn.close()

    def get_channels(self, channel_type='request'):
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM channels WHERE channel_type=?',(channel_type,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def delete_channel(self, channel_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM channels WHERE channel_id=?',(channel_id,))
        conn.commit(); conn.close()

    # ── Payments ───────────────────────────────────────────────────────────
    def add_payment(self, user_id, amount, photo):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('INSERT INTO payments (user_id,amount,photo) VALUES (?,?,?)',(user_id,amount,photo))
        pid = cur.lastrowid; conn.commit(); conn.close(); return pid

    def update_payment_status(self, payment_id, status):
        conn = self.get_connection()
        conn.execute('UPDATE payments SET status=? WHERE id=?',(status,payment_id))
        conn.commit(); conn.close()

    # ── Settings ───────────────────────────────────────────────────────────
    def get_setting(self, key):
        conn = self.get_connection()
        row = conn.execute('SELECT value FROM bot_settings WHERE key=?',(key,)).fetchone()
        conn.close(); return row[0] if row else None

    def update_setting(self, key, value):
        conn = self.get_connection()
        conn.execute('INSERT OR REPLACE INTO bot_settings (key,value) VALUES (?,?)',(key,value))
        conn.commit(); conn.close()

    # ── Stats ──────────────────────────────────────────────────────────────
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
        }
        conn.close(); return s