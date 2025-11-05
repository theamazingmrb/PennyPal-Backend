
from rest_framework import generics, permissions
from accounts.models import BillDue
from accounts.api.serializers import BillDueSerializer 

class BillDueListCreateView(generics.ListCreateAPIView):
    serializer_class = BillDueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = BillDue.objects.filter(user=user)

        # Optional filtering by date
        due_date = self.request.query_params.get('due_date')
        if due_date:
            queryset = queryset.filter(due_date=due_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)