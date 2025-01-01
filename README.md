<h1 align="center">Todo List Web App</h1>

![Create Task](https://github.com/NAHIAN-19/Todo-List-Django/blob/main/Screenshots/create-task.png "Create Task")

## Live Link: [Todo List](https://todo19.vercel.app/)

*Please note that the PDF download feature is different in the live version due to additional dependencies required by [weasyprint](https://pypi.org/project/weasyprint/).*

## Table of Contents
- [Tech Stack](#tech_stack)
- [Installation](#installation)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

# 💻 Tech Stack:
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) 
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)

## Installation

### Cloning from GitHub Repository

To get started with the Todo_List Django Web App, you can clone the repository from GitHub using the following steps:
 
1. **Clone the repository**:

   ```bash
   git clone https://github.com/NAHIAN-19/Todo-List-Django.git
   ```

2. **Install the GTK Installer** (To use weasyprint):

   [GTK Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe)

3. **Navigate to the project folder**:

   ```bash
   cd Todo_List
   ```

4. **Create and activate a virtual environment** (optional but recommended):

   ```bash
   python -m venv myworld
   source myworld/bin/activate  # On Windows use: myworld\Scripts\activate.bat
   ```

5. **Install project dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

6. **Create a .env file in your project root & add keys**:

   ```bash
   python generate_keys.py
   ```

7. **Install Redis**:

   - For Windows: Follow this guide to install Redis: [Install Redis on Windows](https://redis.io/docs/getting-started/installation/install-redis-on-windows/)
   - For MacOS: Use Homebrew:

     ```bash
     brew install redis
     ```

   - For Linux: Use the following commands:

     ```bash
     sudo apt-get update
     sudo apt-get install redis-server
     ```

   - Start Redis server:

     - For Windows: Run `redis-server` from the Redis installation folder.
     - For MacOS/Linux: Run the following:

       ```bash
       redis-server
       ```

8. **Check .env file and follow the link for Email setup**:

   [Geekforgeeks email setup in django](https://www.geeksforgeeks.org/setup-sending-email-in-django-project/)

9. **Start the Celery worker in one terminal window**:

   ```bash
   celery -A Todo_List worker --loglevel=info
   ```

   - Start the Celery Beat scheduler in another terminal window:

     ```bash
     celery -A Todo_List beat --loglevel=info
     ```

10. **Run database migrations**:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

11. **Create a superuser account (for admin access)**:

    ```bash
    python manage.py createsuperuser
    ```

12. **Start the development server**:

    ```bash
    python manage.py runserver
    ```

13. **Open your web browser and go to** [http://localhost:8000](http://localhost:8000) **to access the Todo_List Django Web App**.

## Features

The Todo_List Django Web App offers the following features:

- **Task Management**: Easily add, edit, and delete tasks.
- **Task Prioritization**: Assign priority levels to tasks.
- **Task Categorization**: Divide tasks into different categories.
- **Task Reminder**: Send Email to users for specific tasks (with Celery).
- **User Authentication**: Secure account management (signin, signup, forgot password).
- **Admin Dashboard**: Access admin dashboard [http://localhost:8000/todo-admin/](http://localhost:8000/todo-admin/) to manage users and tasks.
- **Profile Management**: View/Change user details.
- **Export Task Details**: Download PDF / CSV file of your tasks.
- **Dark Mode**: Trigger Dark theme for an awesome experience.

## Contributing

We welcome contributions to improve the Todo_List Django Web App. If you'd like to contribute, please follow these guidelines:

1. Fork the repository.

2. Create a new branch for your feature or bug fix.

3. Make your changes and test them thoroughly.

4. Submit a pull request with a clear description of your changes.

5. Ensure your code follows best practices and includes necessary tests if applicable.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
