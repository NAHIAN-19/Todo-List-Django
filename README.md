<h1 align="center">Todo List Web App</h1>

![Create Task](https://github.com/NAHIAN-19/Todo-List-Django/blob/main/Screenshots/Create_task.png "Create Task")

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
   
2. Navigate to the project folder:
   ```bash
   cd Todo_List
   
3. Create and activate a virtual environment (optional but recommended):
   ```bash
   py -m venv myworld
   myworld\Scripts\activate.bat
4. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   
5. Run database migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   
7. Create a superuser account (for admin access)
   ```bash
   python manage.py createsuperuser
   
8. Start the development server:
   ```bash
   python manage.py runserver
   
9. Open your web browser and go to http://localhost:8000 to access the Todo_List Django Web App.
### Installing from ZIP Archive

1. Download the zip file <a href="https://github.com/NAHIAN-19/Todo-List-Django/blob/main/Todo_List.zip">Todo_List.zip</a>
2. Extract the ZIP archive to your desired location on your computer.
4. Navigate to the project folder:
   --Right click on the project folder and 'Copy as path' and paste the path like below
   ```bash
   cd project_path
6. Continue with steps 3 to 8 from the "Cloning from GitHub Repository" section to set up and run the project

## Features

The Todo_List Django Web App offers the following features:

- **Task Management**: Easily add, edit, and delete tasks.
- **Task Prioritization**: Assign priority levels to tasks.
- **Task Categorization**: Divide tasks in different categories
- **User Authentication**: Secure account management.
- **Admin Dashboard**: Access admin dashboard [http://localhost:8000/admin/](http://localhost:8000/admin/) to manage users and tasks.
- **Profile Managemet**: Change user details(photo,email,pass,name etc).
- **Export Task Details**: Download PDF / CSV file of you tasks.
- **Dark Mode**: Trigger Dark theme for awesome experience.

## Contributing

We welcome contributions to improve the Todo_List Django Web App. If you'd like to contribute, please follow these guidelines:

1. Fork the repository.

2. Create a new branch for your feature or bug fix.

3. Make your changes and test them thoroughly.

4. Submit a pull request with a clear description of your changes.

5. Ensure your code follows best practices and includes necessary tests if applicable.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
