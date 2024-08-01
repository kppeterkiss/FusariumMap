IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'test')
BEGIN
    CREATE DATABASE [test];
END

