# Jewelerly Platform Backend

Its a **Eccomerce application system** built with **Django** and **PostgreSQL**that allows an **Buyers** to make their purchase and inlcude a variety of jewelerly they can choose from.

## Getting Started

Follow these steps to clone the repository and run the server on your local machine.

### 1. Clone the repository

```bash
git clone https://github.com/marywam/manhattan-shop_backend.git

cd manhattan-shop

```

### 2. Set up the virtual environment

```bash
python3 -m venv <your-env-name>
source <your-env-name>/bin/activate

# 👉 **Example**
python3 -m venv virtual
source virtual/bin/activate

```

### 3. Upgrade pip (recommended)

```bash
python -m pip install --upgrade pip

```

### 4. Install Django

```bash
pip install django

```

### 5. Create the Django project

```bash
python -m django startproject shoptech

cd shoptech

```

### 6. Create a Django app

```bash
django-admin startapp shoptechApp

```

### 7. Create a requirements file

```bash
cd ..
touch requirements.txt

```

### 8. Install essential packages

```bash
pip install djangorestframework
pip install django-cors-headers
pip install python-dotenv

```

### 9. Update Django settings

```python
# settings.py

INSTALLED_APPS = [
    # other default apps...
    'rest_framework',
    'corsheaders',
    'shoptechApp',
]

MIDDLEWARE = [
    # other default middleware...
    'corsheaders.middleware.CorsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

```

### 10. Freeze dependencies and push to Git

```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add REST framework and dependencies"
git push

```

### 11. Setting Up PostgreSQL for Your Django Project

```bash
#Install PostgreSQL server & client tools
sudo dnf install postgresql-server postgresql-contrib

# Initialize the database
sudo postgresql-setup --initdb

# Enable and start PostgreSQL service
sudo systemctl enable postgresql
sudo systemctl start postgresql

#Check if it's running
sudo systemctl status postgresql

#Log in to PostgreSQL
💡By default, PostgreSQL creates a system user postgres.
#Switch to that user: 
sudo -i -u postgres

#Now open the PostgreSQL shell
psql

#You should see something like:
postgres=#

#Create a Database and User
💡Inside psql, run these commands:
#Create a new database for your Django project 
CREATE DATABASE  db_name;

#Create a new PostgreSQL user with password 
CREATE USER db_user WITH PASSWORD 'yourpassword';

#Grant privileges to the new user on the database 
GRANT ALL PRIVILEGES ON DATABASE db_name TO db-user;

#Exit psql
\q

#Then exit the postgres user:
exit

#Install PostgreSQL adapter for Django
#In your virtual environment inside your project
install psycopg2

# Install psycopg2 (PostgreSQL adapter for Django)
pip install psycopg2-binary

#Install python-decouple
💡This package lets Django read secrets from a .env file.
#Run this in your virtual environment
pip install python-decouple

✅ Create a .env file
#In your Django project root folder (where manage.py lives), create a file named
.env

#Inside it, add your database credentials and secret key. 
✅ Generate a new secret key--
#Run this command inside your Django project folder 
#(with your virtual environment active)
python -c "from django.core.management.utils import 
get_random_secret_key; print(get_random_secret_key())"

SECRET_KEY=your-django-secret-key

DB_NAME=your_db_name
DB_USER=your_db_user  #by default use postgres
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=5432

✅ Open your Django settings.py file and modify it to use values from .env.
from decouple import config

SECRET_KEY = config("SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

✅ Add .env to .gitignore
.env

✅ Update your requirements.txt
pip freeze > requirements.txt


```

### 12. Run initial migrations

```bash
cd agritech
python manage.py makemigrations agriTechApp
python manage.py migrate agriTechApp

python manage.py migrate

```

### 13. Create a superuser (Admin Account)

```bash
python manage.py createsuperuser

```

You'll be prompted to enter:

- **Username**  
- **Email address**  
- **Password**

Once created, log in at:
<http://127.0.0.1:8000/admin>

> 💡 This account gives you full access to manage farmers, crops, and cooperative records via the Django admin interface.

### 14. Start the development server

```bash
python manage.py runserver

```

## ✅ You're Live

Visit <http://127.0.0.1:8000> to access the development server.
