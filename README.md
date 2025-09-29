# 🎓 Academic Project Management System (APMS)

A full-stack web application built using **Django** for managing academic projects in educational institutions. The system streamlines the process of student project submissions, mentor assignments, document uploads, and progress tracking through a role-based interface for **students**, **teachers (mentors)**, and **administrators**.

## 🚀 Features

- 🔐 **User Authentication & Role-Based Access**
  - Supports three roles: Admin, Teacher (Mentor), and Student
  - Secure login/logout functionality
  - Profile management for students and teachers

- 👥 **Student Module**
  - Register and create/join project groups (3–4 members)
  - Submit project title, problem statement, description
  - Upload required documents: **PPT, SRS, Synopsis, Final Report**

- 🛠️ **Admin Module**
  - Admin dashboard to manage users and project workflows
  - Assign teachers (mentors) to student groups
  - Monitor group submissions and project progress

- 🧑‍🏫 **Teacher (Mentor) Module**
  - View assigned student groups and submitted documents
  - Download uploaded files
  - Filter projects by **class, enrollment number, teacher name, project title**

- 📄 **PDF Generation**
  - Generate and download project details and reports as PDF using **ReportLab**

- 🎨 **Responsive UI**
  - Clean and responsive front-end using **HTML, CSS, Bootstrap, JavaScript**

- 🧩 **Architecture**
  - Built on the **MVC pattern** using Django
 

## 🛠️ Tech Stack

| Layer         | Technologies |
|---------------|--------------|
| Framework     | Django (Python) |
| Frontend      | HTML, CSS, Bootstrap, JavaScript |
| Backend       | Python (Django Views & Models) |
| Database      | SQLite |
| PDF Export    | ReportLab / FPDF |
| Auth System   | Django Authentication System |


## 💾 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rishee10/Academic-Project-Management-System-APMS-.git
   cd Academic-Project-Management-System-APMS-
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ````

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Start the server**
   ```bash
   python manage.py runserver
   ```


   
