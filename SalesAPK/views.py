from django.shortcuts import render,redirect
from django.views import View
from . models import Customer,SalesExpense,Budget
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password 
from django.contrib import messages
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import os
import csv
from django.http import HttpResponse


class Dashboard_view(View):
    def get(self,request):
        if 'user_id' not in request.session:
            return redirect('login')
        
        user_id = request.session['user_id']
        data, df = self.analyze_data(user_id)

        if data:
            self.generate_charts(data, user_id)

        budget_alert=self.budget_alert(user_id)

        return render(request, "dashboard.html", {
            "data": data,
            "charts": {
                "daily_line_chart": f"static/user_{user_id}/daily_line_chart.png",
                "expense_pie_chart": f"static/user_{user_id}/expense_pie_chart.png",
                "sales_expenses_bar_chart": f"static/user_{user_id}/sales_expenses_bar_chart.png",
            },
            "budget_alert":budget_alert

        })
    
    
    def budget_alert(self,user_id):
        budgets=Budget.objects.filter(user_id=user_id)
        expenses=SalesExpense.objects.filter(user_id=user_id)
        total_expense_category={}

        for expense in expenses:
            if expense.category in total_expense_category:
                total_expense_category[expense.category]+=expense.expense_amount
            else:
                total_expense_category[expense.category]=expense.expense_amount
        
        alerts=[]
        for budget in budgets:
            category=budget.category
            monthly_budget=budget.monthly_budget
            total_expense=total_expense_category.get(category,0)

            if total_expense>monthly_budget:
                alerts.append({
                    "category":category,
                    "total_expense":total_expense,
                    "monthly_budget":monthly_budget,
                    "alert_message": f"Exceeded budget for {category}. Total: {total_expense}, Budget: {monthly_budget}",
                })
            
        return alerts

     

        
    def analyze_data(self,user_id):
        customer=Customer.objects.get(id=user_id) 
        records=SalesExpense.objects.filter(user=customer)

        data_list = [
        {
            'user': record.user.name,
            'date': record.date,
            'sales_amount': record.sales_amount,
            'expense_amount': record.expense_amount,
            'category':record.category,
        }
        for record in records
       ]
    
        df=pd.DataFrame(data_list)
        print("records=>,",data_list)
        print("datafrme=>",df)
        
        if df.empty:
            return {},None
        
        total_sales=df['sales_amount'].sum()
        total_expenses=df['expense_amount'].sum()
        profit_or_loss=total_sales-total_expenses

        daily_summary=df.groupby('date').sum()

        expense_by_category=df.groupby('category')['expense_amount'].sum()

        return (
            {
            "total_sales": total_sales,
            "total_expenses": total_expenses,
            "profit_or_loss": profit_or_loss,
            "daily_summary": daily_summary,
            "expense_by_category": expense_by_category,
            }, df
            )


    def generate_charts(self, data, user_id):   
   
       base_dir = os.path.join("static", f"user_{user_id}")
       os.makedirs(base_dir, exist_ok=True)
   
       #  Daily Line Chart
       daily_summary = data["daily_summary"]
       plt.figure(figsize=(10, 6))
       daily_summary.plot(y=["sales_amount", "expense_amount"], kind="line", marker='o')
       plt.title("Daily Sales and Expenses", fontsize=16)
       plt.xlabel("Date", fontsize=12)
       plt.ylabel("Amount", fontsize=12)
       plt.xticks(rotation=45, fontsize=10)
       plt.legend(["Sales", "Expenses"], loc="upper left")
       plt.grid(visible=True, linestyle='--', alpha=0.5)
       plt.tight_layout()
       plt.savefig(os.path.join(base_dir, "daily_line_chart.png"))
       plt.close()

        # Expense Breakdown Pie Chart
       expense_by_category = data["expense_by_category"]
       plt.figure(figsize=(8, 8))
       expense_by_category.plot(kind="pie", autopct='%1.1f%%', startangle=90, legend=False, textprops={'fontsize': 10})
       plt.title("Expense Breakdown", fontsize=16)
       plt.ylabel("")  # Remove default ylabel for better aesthetics
       plt.tight_layout()
       plt.savefig(os.path.join(base_dir, "expense_pie_chart.png"))
       plt.close()

       #Sales vs Expenses
       plt.figure(figsize=(10, 6))
       daily_summary.plot(y=["sales_amount", "expense_amount"], kind="bar", alpha=0.8, width=0.8)
       plt.title("Sales vs Expenses", fontsize=16)
       plt.xlabel("Date", fontsize=12)
       plt.ylabel("Amount", fontsize=12)
       plt.xticks(rotation=45, fontsize=10)
       plt.legend(["Sales", "Expenses"], loc="upper left")
       plt.grid(visible=True, linestyle='--', alpha=0.5)
       plt.tight_layout()
       plt.savefig(os.path.join(base_dir, "sales_expenses_bar_chart.png"))
       plt.close()



class Login_view(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        email = request.POST.get('email') 
        password = request.POST.get('password')

        try:
           
            obj = Customer.objects.get(email=email)

            if check_password(password, obj.password):
                request.session['user_id'] = obj.id
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
                return render(request, "login.html")
        except Customer.DoesNotExist:
            messages.error(request, "User not found. Please check your email.")
            return render(request, "login.html")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, "login.html")
        


class Signup_view(View):
    def get(self, request):
        return render(request, "signup.html")

    def post(self, request):
        try:
           
            name = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')

          
            if not name or not email or not password:
                return render(request, "signup.html", {'error': "All fields are required!"})

            
            hashed_password = make_password(password)
            customer = Customer.objects.create(name=name, email=email, password=hashed_password)
            customer.save()        
           
            return redirect('login') 
        except Exception as e:
            return render(request, "errorpage.html", {'error': "An error occurred. Please try again later."})


class LogOut_view(View):
    def get(self,request):
        request.session.pop('user_id', None)
        redirect('signup')

    def post(self,request):
        pass


class InputView(View):
    def get(self,request):
        if 'user_id' not in request.session:
            return redirect('login')
        return render(request,"input_form.html")
    
    def post(self,request):
        try:
            user=Customer.objects.get(id=request.session['user_id'])
            date=request.POST.get('date')
            sales_amount=request.POST.get('sales_amount')
            expense_amount=request.POST.get('expense_amount')
            category=request.POST.get('category')

            SalesExpense.objects.create(
                user=user,
                date=date,
                sales_amount=sales_amount,
                expense_amount=expense_amount,
                category=category
                )
            
            return redirect('dashboard')
        except Exception as e:
             messages.error(request, f"Error: {str(e)}")
             return render(request, "input_form.html")

class Import_Excel_Csv(View):
    
    def get(self,request):
        return render(request, 'import_csv.html')
    
    def get_extension(self,file):
        return file.name.split('.')[-1].lower()
    
    def post(self,request):
        
        if request.FILES.get('file'):
            file = request.FILES['file']
            try:
                if self.get_extension(file)=='csv':
                    df=pd.read_csv(file)
                elif self.get_extension(file)=='xlsx':
                    df=pd.read_excel(file)
                else:
                    messages.error(request,"Import a valid File CSV/XLSX")
                    return redirect('/')
            
                required_columns = ['Date', 'SalesAmount', 'ExpenseAmount', 'Category']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    messages.error(request,f"missing required columns : {','.join(missing_columns)}")
                
                user=Customer.objects.get(id=request.session['user_id'])

                for _, row in df.iterrows():
                    SalesExpense.objects.create(
                        user=user,
                        date=pd.to_datetime(row['Date'], errors='coerce'),
                        sales_amount=row['SalesAmount'],
                        expense_amount=row['ExpenseAmount'],
                        category=row['Category'],
                    )

                messages.success(request,"file imported sucessfully")
            except Exception as e:
                messages.error(request, f"Error importing file: {str(e)}")
        else:
            messages.error(request,"No file uploaded . Please select a file")
            

        return redirect('/')
        
    

class Export_Excel_Csv(View):
    def get(self, request):
        try:
            
            records = SalesExpense.objects.filter(user_id=request.session.get('user_id'))
            
            if not records.exists():
                messages.error(request, "No records found to export.")
                return redirect('dashboard')  

            #DataFrame from the queryset
            data = [
                {
                    "Date": record.date,
                    "SalesAmount": record.sales_amount,
                    "ExpenseAmount": record.expense_amount,
                    "Category": record.category,
                }
                for record in records
            ]
            df = pd.DataFrame(data)

           
            file_format = request.GET.get("format", "csv").lower() 

            if file_format == "csv":
                response = HttpResponse(content_type="text/csv")
                response['Content-Disposition'] = 'attachment; filename="sales_expense_records.csv"'
                df.to_csv(response, index=False)
            elif file_format == "xlsx":
                response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                response['Content-Disposition'] = 'attachment; filename="sales_expense_records.xlsx"'
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
            else:
                messages.error(request, "Invalid file format. Choose 'csv' or 'xlsx'.")
                return redirect('dashboard') 

            return response

        except Exception as e:
            messages.error(request, f"Error exporting file: {e}")
            return redirect('dashboard') 
        
class ManageBudgets(View):
    def get(self,request):
        user_id = request.session.get('user_id')
        budgets = Budget.objects.filter(user_id=user_id)
        return render(request,"budget_management.html",{'budgets':budgets})

    def post(self,request):
        user_id=request.session.get('user_id')
        if user_id is None:
           messages.error(request, "You must be logged in to add a budget.")
           return redirect('login')
        
        try:
           category=request.POST.get('category')
           monthly_budget=request.POST.get('monthly_budget')

           if not category or not monthly_budget:
              messages.error(request,"all fields are required")

           monthly_budget=float(monthly_budget) 
           Budget.objects.create(
               user_id=user_id,
               category=category,
               monthly_budget=monthly_budget,
           )

           messages.success(request,"Budget added sucessfully")
        except Exception as e:
             messages.error(request,f"An error occurred: {str(e)}")
        return redirect('manage_budgets')
    
    

         



            
