import factory

from django.utils import timezone
from faker import Faker

fake = Faker()


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "group.Group"

    id = factory.Faker("uuid4")
    name = factory.Faker("company")
    owner = factory.SubFactory("tests.factories.user_factory.UserFactory")
    is_private = False
    created_at = factory.LazyFunction(lambda: timezone.now())
    updated_at = factory.LazyFunction(lambda: timezone.now())
