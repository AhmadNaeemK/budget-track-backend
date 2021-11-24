from datetime import datetime

from django.db.models import Sum
from django.template.loader import get_template

from .models import Transaction, TransactionCategories
from .serializers import TransactionSerializer


class ReportMaker:

    def __init__(self, request_data):
        self.from_date = datetime.strptime(request_data.get('from_date')[0], '%Y-%m-%d').date()
        self.to_date = datetime.strptime(request_data.get('to_date')[0], '%Y-%m-%d').date()
        self.user_id = request_data.get('user_id')
        self.type = request_data.get('report_type')[0]

    def make_report(self):
        if self.type == 'csv':
            return self._generate_csv_report()

    def _get_transactions_data(self):
        transactions = Transaction.objects.filter(
            user=self.user_id,
            transaction_time__range=(self.from_date, self.to_date),
        )
        total_deposit = transactions.filter(category=TransactionCategories.Income.value
                                            ).aggregate(Sum('amount'))['amount__sum']
        total_withdrawal = transactions.exclude(category=TransactionCategories.Income.value
                                                ).aggregate(Sum('amount'))['amount__sum']
        transactions = TransactionSerializer(transactions, many=True).data
        return {'transactions': transactions,
                'total_deposit': total_deposit,
                'total_withdrawal': total_withdrawal}

    def _generate_csv_report(self):
        report_data = self._get_transactions_data()
        csv_template = get_template('reports/transactionReportTemplate.txt')
        csv = csv_template.render(report_data)
        return csv
