CREATE TYPE playlist_visibility AS ENUM ('private', 'public', 'shared');

CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	name VARCHAR(255),
	email VARCHAR(255) UNIQUE NOT NULL,
	is_admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE artists (
	id SERIAL PRIMARY KEY,
	name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE songs (
	id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	artist_id INT NOT NULL,
	uploaded_by INT NOT NULL,
	sha256_hash VARCHAR(255) NOT NULL,
	db_path VARCHAR(255) NOT NULL,
	FOREIGN KEY (artist_id) REFERENCES artists(id),
	FOREIGN KEY (uploaded_by) REFERENCES users(id),
	CONSTRAINT fk_artist FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
	CONSTRAINT fk_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE albums (
	id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	artist_id INT NOT NULL,
	FOREIGN KEY (artist_id) REFERENCES artists(id),
	CONSTRAINT unique_album UNIQUE (artist_id, title)
);

CREATE TABLE album_songs (
	album_id INT NOT NULL,
	song_id INT NOT NULL,
	PRIMARY KEY (album_id, song_id),
	FOREIGN KEY (album_id) REFERENCES albums(id),
	FOREIGN KEY (song_id) REFERENCES songs(id)
);

CREATE TABLE playlists (
	id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	owner_id INT NOT NULL,
	visibility playlist_visibility DEFAULT 'private',
	FOREIGN KEY (owner_id) REFERENCES users(id),
	CONSTRAINT unique_playlist UNIQUE (owner_id, title)
);

CREATE TABLE playlist_songs (
	playlist_id INT NOT NULL,
	position INT NOT NULL,
	song_id INT NOT NULL,
	added_by INT NOT NULL,
	PRIMARY KEY (playlist_id, position),
	FOREIGN KEY (playlist_id) REFERENCES playlists(id),
	FOREIGN KEY (song_id) REFERENCES songs(id),
	FOREIGN KEY (added_by) REFERENCES users(id)
);

CREATE TABLE playlist_shares (
	playlist_id INT NOT NULL,
	user_id INT NOT NULL,
	is_editor BOOLEAN DEFAULT FALSE,
	PRIMARY KEY (playlist_id, user_id),
	FOREIGN KEY (playlist_id) REFERENCES playlists(id),
	FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_songs_artist_id ON songs (artist_id);
CREATE INDEX idx_songs_uploaded_by ON songs (uploaded_by);
CREATE INDEX idx_songs_sha256_hash ON songs (sha256_hash);

CREATE INDEX idx_albums_artist_id ON albums (artist_id);

CREATE INDEX idx_playlists_owner_id ON playlists (owner_id);
CREATE INDEX idx_playlists_visibility ON playlists (visibility);

CREATE INDEX idx_playlists_songs_song_id ON playlist_songs (song_id);
CREATE INDEX idx_playlist_songs_added_by ON playlist_songs (added_by);

CREATE INDEX idx_playlist_shares_user_id ON playlist_shares (user_id);
