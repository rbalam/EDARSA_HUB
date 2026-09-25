SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 51000, 'ABORT_WRONG_DATABASE', 1;

IF SUSER_SNAME() = 'HRLectura'
    THROW 51001, 'ABORT_READONLY_LOGIN_NOT_WRITER', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Services_Professions','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Services_Professions(
            ProfessionID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Services_Professions PRIMARY KEY,
            Codigo varchar(50) NOT NULL,
            Nombre nvarchar(150) NOT NULL,
            Activo bit NOT NULL CONSTRAINT DF_Services_Professions_Activo DEFAULT(1),
            CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Services_Professions_CreatedAt DEFAULT(SYSUTCDATETIME()),
            UpdatedAt datetime2(0) NULL,
            CONSTRAINT UQ_Services_Professions_Codigo UNIQUE(Codigo)
        );
    END;

    IF OBJECT_ID('dbo.Services_Specialties','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Services_Specialties(
            SpecialtyID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Services_Specialties PRIMARY KEY,
            ParentSpecialtyID bigint NULL,
            Codigo varchar(50) NOT NULL,
            Nombre nvarchar(150) NOT NULL,
            Activo bit NOT NULL CONSTRAINT DF_Services_Specialties_Activo DEFAULT(1),
            CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Services_Specialties_CreatedAt DEFAULT(SYSUTCDATETIME()),
            UpdatedAt datetime2(0) NULL,
            CONSTRAINT UQ_Services_Specialties_Codigo UNIQUE(Codigo),
            CONSTRAINT CK_Services_Specialties_NoSelfParent CHECK (ParentSpecialtyID IS NULL OR ParentSpecialtyID <> SpecialtyID),
            CONSTRAINT FK_Services_Specialties_Parent FOREIGN KEY(ParentSpecialtyID) REFERENCES dbo.Services_Specialties(SpecialtyID)
        );
    END;

    COMMIT;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK;
    THROW;
END CATCH;
