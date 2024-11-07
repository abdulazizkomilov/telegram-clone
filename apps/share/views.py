from rest_framework import generics, status, permissions
from rest_framework.response import Response
from .documents import UserIndex, GroupIndex, ChannelIndex


class SearchView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = kwargs.get("query")

        if not query:
            return Response(
                {"error": "Query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_results = (
            UserIndex.search()
            .query(
                "multi_match",
                query=query,
                fields=["phone_number", "first_name", "last_name"],
            )
            .execute()
        )

        group_results = GroupIndex.search().query("match", name=query).execute()

        channel_results = (
            ChannelIndex.search()
            .query("multi_match", query=query, fields=["name", "description"])
            .execute()
        )

        results = {
            "users": [hit.to_dict() for hit in user_results],
            "groups": [hit.to_dict() for hit in group_results],
            "channels": [hit.to_dict() for hit in channel_results],
        }

        return Response(results, status=status.HTTP_200_OK)
