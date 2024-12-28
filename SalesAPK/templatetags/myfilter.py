from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def format_budget_alert(monthly_budget,total_expense):
    exceeded_amount = float(total_expense)-float(monthly_budget)
    return exceeded_amount if exceeded_amount > 0 else 0
