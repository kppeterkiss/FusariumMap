
USE [master]

/* Users are typically mapped to logins, as OP's question implies,
so make sure an appropriate login exists. */
IF NOT EXISTS(SELECT principal_id FROM sys.server_principals WHERE name = '$MSSQL_PYTHON_U') BEGIN
    /* Syntax for SQL server login.  See BOL for domain logins, etc. */
    CREATE LOGIN $MSSQL_PYTHON_U
    WITH PASSWORD = '$MSSQL_PYTHON_PW'
END



/* Users are typically mapped to logins, as OP's question implies,
so make sure an appropriate login exists. */
IF NOT EXISTS(SELECT principal_id FROM sys.server_principals WHERE name = '$MSSQL_ARCGIS_U') BEGIN
    /* Syntax for SQL server login.  See BOL for domain logins, etc. */
    CREATE LOGIN $MSSQL_ARCGIS_U
    WITH PASSWORD = '$MSSQL_ARCGIS_PW'
END



USE [odp]
/* Create the user for the specified login. */
IF NOT EXISTS(SELECT principal_id FROM sys.database_principals WHERE name = '$MSSQL_PYTHON_U') BEGIN
    CREATE USER $MSSQL_PYTHON_U FOR LOGIN $MSSQL_PYTHON_U
END




/* Create the user for the specified login. */
IF NOT EXISTS(SELECT principal_id FROM sys.database_principals WHERE name = '$MSSQL_ARCGIS_U') BEGIN
    CREATE USER $MSSQL_ARCGIS_U FOR LOGIN $MSSQL_ARCGIS_U
END


ALTER ROLE [db_owner] ADD MEMBER $MSSQL_PYTHON_U


ALTER ROLE [db_owner] ADD MEMBER $MSSQL_ARCGIS_U


