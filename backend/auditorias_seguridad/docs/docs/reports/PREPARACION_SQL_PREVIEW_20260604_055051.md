# PREPARACIÓN SQL PREVIEW
Fecha: Thu Jun  4 05:50:51 UTC 2026

## 1. Sistema operativo
```text
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```
## 2. IP pública de salida del contenedor
```text
34.170.12.145
```
## 3. Instalar dependencias ODBC si faltan
```text
Hit:1 https://deb.nodesource.com/node_20.x nodistro InRelease
Hit:2 https://cloudfront.debian.net/debian bookworm InRelease
Get:3 https://cloudfront.debian.net/debian bookworm-updates InRelease [55.4 kB]
Get:4 https://cloudfront.debian.net/debian-security bookworm-security InRelease [48.0 kB]
Hit:5 https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 InRelease
Get:6 https://cloudfront.debian.net/debian-security bookworm-security/main arm64 Packages [303 kB]
Fetched 406 kB in 1s (695 kB/s)
Reading package lists...
Reading package lists...
Building dependency tree...
Reading state information...
curl is already the newest version (7.88.1-10+deb12u14).
gnupg is already the newest version (2.2.40-1.1+deb12u2).
gnupg set to manually installed.
The following additional packages will be installed:
  libltdl7 libodbc2 libodbccr2 libodbcinst2 unixodbc-common
Suggested packages:
  odbc-postgresql tdsodbc
The following NEW packages will be installed:
  apt-transport-https libltdl7 libodbc2 libodbccr2 libodbcinst2 unixodbc
  unixodbc-common unixodbc-dev
0 upgraded, 8 newly installed, 0 to remove and 10 not upgraded.
Need to get 849 kB of archives.
After this operation, 3176 kB of additional disk space will be used.
Get:1 https://cloudfront.debian.net/debian bookworm/main arm64 apt-transport-https all 2.6.1 [25.2 kB]
Get:2 https://cloudfront.debian.net/debian bookworm/main arm64 libltdl7 arm64 2.4.7-7~deb12u1 [392 kB]
Get:3 https://cloudfront.debian.net/debian bookworm/main arm64 libodbc2 arm64 2.3.11-2+deb12u1 [132 kB]
Get:4 https://cloudfront.debian.net/debian bookworm/main arm64 libodbccr2 arm64 2.3.11-2+deb12u1 [16.4 kB]
Get:5 https://cloudfront.debian.net/debian bookworm/main arm64 unixodbc-common all 2.3.11-2+deb12u1 [8172 B]
Get:6 https://cloudfront.debian.net/debian bookworm/main arm64 libodbcinst2 arm64 2.3.11-2+deb12u1 [35.2 kB]
Get:7 https://cloudfront.debian.net/debian bookworm/main arm64 unixodbc arm64 2.3.11-2+deb12u1 [26.3 kB]
Get:8 https://cloudfront.debian.net/debian bookworm/main arm64 unixodbc-dev arm64 2.3.11-2+deb12u1 [214 kB]
debconf: delaying package configuration, since apt-utils is not installed
Fetched 849 kB in 0s (3546 kB/s)
Selecting previously unselected package apt-transport-https.
(Reading database ... (Reading database ... 5%(Reading database ... 10%(Reading database ... 15%(Reading database ... 20%(Reading database ... 25%(Reading database ... 30%(Reading database ... 35%(Reading database ... 40%(Reading database ... 45%(Reading database ... 50%(Reading database ... 55%(Reading database ... 60%(Reading database ... 65%(Reading database ... 70%(Reading database ... 75%(Reading database ... 80%(Reading database ... 85%(Reading database ... 90%(Reading database ... 95%(Reading database ... 100%(Reading database ... 43967 files and directories currently installed.)
Preparing to unpack .../0-apt-transport-https_2.6.1_all.deb ...
Unpacking apt-transport-https (2.6.1) ...
Selecting previously unselected package libltdl7:arm64.
Preparing to unpack .../1-libltdl7_2.4.7-7~deb12u1_arm64.deb ...
Unpacking libltdl7:arm64 (2.4.7-7~deb12u1) ...
Selecting previously unselected package libodbc2:arm64.
Preparing to unpack .../2-libodbc2_2.3.11-2+deb12u1_arm64.deb ...
Unpacking libodbc2:arm64 (2.3.11-2+deb12u1) ...
Selecting previously unselected package libodbccr2:arm64.
Preparing to unpack .../3-libodbccr2_2.3.11-2+deb12u1_arm64.deb ...
Unpacking libodbccr2:arm64 (2.3.11-2+deb12u1) ...
Selecting previously unselected package unixodbc-common.
Preparing to unpack .../4-unixodbc-common_2.3.11-2+deb12u1_all.deb ...
Unpacking unixodbc-common (2.3.11-2+deb12u1) ...
Selecting previously unselected package libodbcinst2:arm64.
Preparing to unpack .../5-libodbcinst2_2.3.11-2+deb12u1_arm64.deb ...
Unpacking libodbcinst2:arm64 (2.3.11-2+deb12u1) ...
Selecting previously unselected package unixodbc.
Preparing to unpack .../6-unixodbc_2.3.11-2+deb12u1_arm64.deb ...
Unpacking unixodbc (2.3.11-2+deb12u1) ...
Selecting previously unselected package unixodbc-dev:arm64.
Preparing to unpack .../7-unixodbc-dev_2.3.11-2+deb12u1_arm64.deb ...
Unpacking unixodbc-dev:arm64 (2.3.11-2+deb12u1) ...
Setting up apt-transport-https (2.6.1) ...
Setting up unixodbc-common (2.3.11-2+deb12u1) ...
Setting up libltdl7:arm64 (2.4.7-7~deb12u1) ...
Setting up libodbc2:arm64 (2.3.11-2+deb12u1) ...
Setting up libodbccr2:arm64 (2.3.11-2+deb12u1) ...
Setting up libodbcinst2:arm64 (2.3.11-2+deb12u1) ...
Setting up unixodbc (2.3.11-2+deb12u1) ...
Setting up unixodbc-dev:arm64 (2.3.11-2+deb12u1) ...
Processing triggers for libc-bin (2.36-9+deb12u14) ...
pyodbc import OK
[]
```
## 4. Validar pyodbc post instalación
```text
pyodbc OK
drivers: []
```
