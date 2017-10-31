DROP DATABASE photoshare;
CREATE DATABASE photoshare;
USE photoshare;




CREATE TABLE Users (
  user_id INT AUTO_INCREMENT,
  dob DATE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  hometown VARCHAR(100),
  gender VARCHAR(100),
  password VARCHAR(255) NOT NULL,
  CONSTRAINT users_pk PRIMARY KEY(user_id));
INSERT INTO Users (first_name,last_name,email,password,dob) VALUES ('Guest', 'User','guest@photoshare.com','password',NOW());

CREATE TABLE Album (
  album_id INT AUTO_INCREMENT,
  name CHAR(32),
  user_id INT,
  date_of_creation DATE,
  PRIMARY KEY(album_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE);

CREATE TABLE Pictures
(
  picture_id int  AUTO_INCREMENT,
  user_id int,
  imgpath VARCHAR(255),
  caption VARCHAR(255),
  album_id INT,
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (album_id) REFERENCES Album(album_id) ON DELETE CASCADE
);

CREATE TABLE Comment (
  comment_id INT AUTO_INCREMENT,
  date_left DATE,
  text VARCHAR(100),
  user_id int,
  picture_id int,
  PRIMARY KEY(comment_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE SET NULL);

CREATE TABLE Tag (
  word VARCHAR(100),
  PRIMARY KEY(word));




CREATE TABLE Likes (
  user_id int,
  picture_id int,
  PRIMARY KEY (user_id, picture_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE);

CREATE TABLE Friends (
  user_id1 INT,
  user_id2 INT,
  since DATE,
  PRIMARY KEY (user_id1, user_id2),
  FOREIGN KEY (user_id1) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id2) REFERENCES Users(user_id) ON DELETE CASCADE);

CREATE TABLE associated_with (
  picture_id INT,
  word VARCHAR(100),
  PRIMARY KEY(picture_id, word),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  FOREIGN KEY (word) REFERENCES Tag(word) ON DELETE CASCADE);



