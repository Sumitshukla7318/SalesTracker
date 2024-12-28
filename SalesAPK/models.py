from django.db import models

class Customer(models.Model):
    name=models.CharField(max_length=100)
    password=models.CharField(max_length=100)
    email=models.CharField(max_length=100)

class SalesExpense(models.Model):
    user=models.ForeignKey(Customer,on_delete=models.CASCADE)
    date=models.DateField()
    sales_amount=models.FloatField()
    expense_amount=models.FloatField()
    category=models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.name} - {self.date}: Sales {self.sales_amount}, Expenses {self.expense_amount}"


class Budget(models.Model):
    user = models.ForeignKey('Customer', on_delete=models.CASCADE) 
    category = models.CharField(max_length=255)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.category} - {self.monthly_budget}"