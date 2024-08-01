USE [master];

IF NOT EXISTS(SELECT * FROM sys.databases WHERE name='odp')
BEGIN
    CREATE DATABASE [odp];
END


