

# 💰 **PennyPal**

### Your Personal Finance Calendar App

![pennypal](https://i.imgur.com/LzPdscp.jpeg)

---

##  **WHY?**
- See all your income, expenses, and balances clearly.  
- Understand your spending habits — how much goes to bills, food, entertainment, etc.  
- Make informed financial decisions instead of guessing.  
- Help stay on top of bills and deadlines.  
- See your expenses organized and easily spot them.  
- Track income and expenses to watch your net balance grow, set finance goals, and see progress weekly or monthly.  
- Build better habits and reduce stress.  

---

##  **MVP User Stories**
- As a new user, I want to **sign up** with name, email, password, and password confirmation so I can create an account.  
- As a registered user, I want to **sign in** securely so I can access my financial tools.
- As a user, I want to **log out securely**. 
- As a user, I want to **delete my account** if I no longer wish to use the app. 
- As a user, I want to **create a monthly calendar** by selecting a month and year to track my finances.  
- As a user, I want to **view my full monthly calendar** to see daily spendings, bills, and credit dues.  
- As a user, I want to **click a day** on my calendar to see detailed spendings and due dates for that day.  
- As a user, I want to **navigate between months** to review past or upcoming spendings.  
- As a user, I want to **add a spending entry** (type, amount, note) to record expenses.  
- As a user, I want to **edit or delete** a spending entry to correct mistakes or remove items.  
- As a user, I want to **see the total amount spent** for the selected day.  
- As a user, I want to **add bills due dates** so I don’t forget payments.  
- As a user, I want to **add credit card due dates** to stay on top of payments.  
- As a user, I want to **see my due dates directly on my calendar** with color-coded markers.  
- As a user, I want to **navigate between months** to review past or upcoming financial activity. 
- As a user, I want to **view a Monthly Summary page with a pie chart** showing income, expenses, and bills.  
- As a user, I want to **view an Annual Summary page with a pie chart** that visualizes my yearly totals 

---

##  **Wireframes**
1. **Welcome Page** – Logo + “Sign Up” / “Sign In” buttons  
2. **Sign Up Page**  
3. **Sign In Page**  
4. **Calendar Page** – Monthly grid with bills, credit, spendings  
5. **Day Details Page** – Table with spending, bills, income with "Edite" / "Delete" / "Add" buttons  
6. **Monthly Summary Page** – Pie chart chart  
7. **Annual Summary Page** – Pie chart 
8. **Profile Page** - User information with "Edit" / "Delete" buttons

---

## API Endpoints

| Endpoint                                 | Method        | Function                     |Description                                           | 
|------------------------------------------|---------------|------------------------------|-------------------------------------------------------
| /api/signup/                             | POST          | CreateUser                   | Register newuser                                     |
| /api/signin/                             | POST          | LoginUser                    | Authenticate user and return token                   |
| /api/logout/                             | GET           | LogoutUser                   | Log out and invalidate current token                 |
| /api/profile/                            | GET           | UserProfileView              | Retrieve logged-in user profile                      |
| /api/profile/update/                     | PUT           | ProfileUpdateView            | Update first name, last name, or email               |
| /api/profile/delete/                     | DELETE        | DeleteAccountView            | Permanently delete user account                      |
| /api/calendar/?month=&year=              | GET           | CalendarListView             | Get or create calendar for selected month/year       |
| /api/calendar/<calendar_id>/day/<date>/  | GET           | DayView                      | View transactions & bills for a specific date        |
| /api/transactions/                       | GET / POST    | TransactionListCreateView    | Retrieve or add income/expense                       |
| /api/transactions/<id>/                  | PUT / DELETE  | TransactionDetailView        | Edit or delete a transaction                         |
| /api/bills/                              | GET / POST    | BillListCreateView           | Retrieve or add bills                                |
| /api/bills/<id>/                         | PUT / DELETE  | BillDetailView               | Edit or delete a bill                                |
| /api/monthly-pie-data/                   | GET           | MonthlyPieDataView           | Data for monthly pie chart (income, expenses, bills) |
| /api/summary/monthly/                    | GET           | MonthlySummaryView           | Monthly totals (income, expenses, bills, balance)    |
| /api/summary/annual/                     | GET           | AnnualSummaryView            | Yearly totals (income, expenses, bills, balance)     | 


##  **Database Schema**
###  User
| Field | Type | Relationship | Notes |
|--------|------|---------------|--------|
| id | AutoField | Primary Key | Unique user ID |
| username | CharField | — | Required, unique |
| email | EmailField | — | User’s email |
| password | CharField | — | Encrypted password |
| password2 | CharField | - | Password confirmation (used only during sign-up) |
| first_name | CharField | - | User’s first name |
| last-name | Chart Field | - | User’s last name |


### Profile
| Field | Type | Relationship | Notes |
|--------|------|---------------|--------|
| id | AutoField | Primary Key | — |
| user | One-to-One(User) | Each profile belongs to one user |


### Category
| Field | Type | Relationship | Notes |
|--------|------|---------------|--------|
| id | AutoField | Primary Key | — |
| user | ForeignKey(User) | One-to-Many | Each user can have multiple categories |
| name | CharField | — | Example: “Groceries” |


###  Transaction
| Field | Type | Relationship | Notes |
|--------|------|---------------|--------|
| id | AutoField | Primary Key | — |
| uses | ForeignKey(User) | One-to-Many | Each Transaction belongs to one user |
| category | CharField | — | Example: “Groceries”, “Transport” |
| type | CharField | — | Enter "income" or "expenses" |
| amount | DecimalField | — | Amount of transaction |
| date | DateField | - | Transaction date |
| description | TextField | — | Optional |


###  BillDue
| Field | Type | Relationship | Notes |
|--------|------|---------------|--------|
| id | AutoField | Primary Key | — |
| user | ForeignKey(User) | One-to-Many | Each bill belongs to one user |
| name | CharField | — | Example: “Rent”, “Electricity” |
| amount | DecimalField | — | Bill Amount |
| due_date | DateField | — | Bill due date |
| note | TextField | — | Optional |
| type | CharField | — | Bill category(Optional) |
| is-paid | BooleanField | — | Mark bill as paid or unpaid |


###  Calendar
| Field | Type | Relationship | Notes |
|--------|------|---------------|--------|
| id | AutoField | Primary Key | — |
| user | ForeignKey(User) | One-to-Many | Each calendar belongs to one user |
| month | CharField | — | Example: “January” |
| year | IntegerField | — | Example: 2025 |


###  CalendarCell
| Field | Type | Relationship | Notes |
|--------|------|---------------|--------|
| id | AutoField | Primary Key | — |
| calendar | ForeignKey(Calendar) | One-to-Many | Each cell belongs to one calendar |
| date | DateField | — | Represents a single day |
| net_balance | DecimalField | — | Optional, calculated dynamically |
| total-expences | DecimalField | — | Calendar from transaction |
| total-income | DecimalField | — | Calendar from transaction |


###  Summaries (Calculated)
| Summary Type | Data Source | Description |
|---------------|--------------|--------------|
| MonthlySummary | Transactions + Bills | Aggregates totals by month |
| AnnualSummary | Transactions + Bills | Aggregates yearly spending |
| Monthky Pie | Transactions + Bills | Provides data for monthly chart visualizations |

---

##  Entity Relationships
| Entity | Description | Relationship |
|--------|--------------|---------------|
| User | Registered person | Has one Profile |
| Profile | User Details | Belong to one user |
| Calendar | Monthly tracker | Belongs to one User |
| CalendarCell | Daily tracker | Belongs to one Calendar |
| Transaction | Income/Expenses record | Belongs to one User |
| BillDue | Bill or payment due | Belongs to one User |
| Category | User-defined transaction category | Belongs to one User |
| Summaries | Calculated | Drived from transactions and bills |

---

##  **Tech Stack**
| Category | Tools |
|-----------|--------|
| Frontend | React, Tailwind CSS, Recharts |
| Backend | Django REST Framework |
| Database | PostgreSQL |
| Deployment | Heroku (Backend), Netlify (Frontend) |
| Version Control | GitHub |
| Utilities | Figma, Postman, VS Code, Trello |

---


## **GITHUB**

https://github.com/MarjiRad/PennyPal-Backend.git
https://github.com/MarjiRad/PennyPal-Frontend.git


## **TRELLO**

https://trello.com/b/1yooqdM0/pennypal


