CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id int  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Pictures
(
  picture_id int  AUTO_INCREMENT,
  user_id int,
  imgdata longblob ,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);

CREATE TABLE Users (user_id INT AUTO_, dob DATE NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, last_name VARCHAR(100) NOT NULL, first_name VARCHAR(100) NOT NULL, hometown VARCHAR(100), gender VARCHAR(100), password VARCHAR(24) NOT NULL, PRIMARY KEY(user_id));

CREATE TABLE Comment (comment_id INT, date_left DATE, text VARCHAR(100), user_id INT, photo_id INT, PRIMARY KEY(comment_id), FOREIGN KEY (user_id) REFERENCES Users(user_id), FOREIGN KEY (photo_id) REFERENCES Photo(photo_id));

CREATE TABLE Tag (word VARCHAR(100), PRIMARY KEY(word));

CREATE TABLE Photo (photo_id INT, caption VARCHAR(140), data VARCHAR(100),  album_id INT, PRIMARY KEY(photo_id), FOREIGN KEY (album_id) REFERENCES Album(album_id) ON DELETE CASCADE);

CREATE TABLE Album (album_id INT, name CHAR(32), user_id INT, date_of_creation DATE, PRIMARY KEY(album_id), FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE);

CREATE TABLE Like (user_id INT, photo_id INT, PRIMARY KEY(user_id, photo_id), FOREIGN KEY(user_id) REFERENCES Users(user_id), FOREIGN KEY (photo_id) REFERENCES Photo(photo_id));

CREATE TABLE Friends (user_id1 INT, user_id2 INT, since DATE, PRIMARY KEY (user_id1, user_id2), FOREIGN KEY (user_id1) REFERENCES Users(user_id), FOREIGN KEY (user_id2) REFERENCES Users(user_id));

CREATE TABLE associated_with (photo_id INT, word VARCHAR(100), PRIMARY KEY(photo_id, word), FOREIGN KEY (photo_id) REFERENCES Photo(photo_id), FOREIGN KEY (word) REFERENCES Tag(word));


INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
