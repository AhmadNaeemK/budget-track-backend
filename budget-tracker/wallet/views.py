from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.http import Http404

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionList(APIView):

    def get(self, *args, **kwargs):
        transactions = Transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        print(serializer)
        return Response(serializer.data)

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
