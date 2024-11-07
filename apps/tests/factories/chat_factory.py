import factory

from django.utils import timezone
from faker import Faker

fake = Faker()


class ChatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "chat.Chat"

    id = factory.Faker("uuid4")
    owner = factory.SubFactory("tests.factories.user_factory.UserFactory")
    user = factory.SubFactory("tests.factories.user_factory.UserFactory")
    created_at = factory.LazyFunction(lambda: timezone.now())
    updated_at = factory.LazyFunction(lambda: timezone.now())
