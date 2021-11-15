from rest_framework import filters


class UserFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        queryset = queryset.filter(user=request.user.id)
        return queryset


class ReceiverFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        queryset = queryset.filter(receiver=request.user.id)
        return queryset
