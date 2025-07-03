CREATE DATABASE IF NOT EXISTS `expenses_project` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `expenses_project`;

CREATE TABLE IF NOT EXISTS `users` (
	`id` int(11) NOT NULL AUTO_INCREMENT,
  	`username` varchar(50) NOT NULL,
  	`password` varchar(255) NOT NULL,
    PRIMARY KEY (`id`)
);


