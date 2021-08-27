from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.backends import TokenBackend

from django.http import Http404
from django.conf import settings

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionList(APIView):

    def get(self, request, format=None):
        if request.GET.get('all') == 'false':
            transactions = Transaction.objects.filter(user_id=request.user.id)[:5]
        else:
            transactions = Transaction.objects.filter(user_id=request.user.id)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

