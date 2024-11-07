import factory

from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker

fake = Faker()

User = get_user_model()


def fake_number():
    country_code = "+99890"
    national_number = fake.numerify(text="#######")
    return f"{country_code}{national_number}"


class UserFactory(factory.django.DjangoModelFactory):
    """This class will create fake data for user"""

    class Meta:
        model = User

    id = factory.Faker("uuid4")
    phone_number = factory.LazyFunction(fake_number)
    first_name = fake.first_name()
    last_name = fake.last_name()
    user_name = factory.Faker("user_name")
    bio = factory.Faker("text")
    is_online = False
    is_staff = False
    is_active = True
    is_verified = True
    is_2fa_enabled = False
    otp_secret = factory.Faker("sha1")

    birth_date = fake.date(pattern="%Y-%m-%d")
    last_seen = factory.LazyFunction(lambda: timezone.make_aware(fake.date_time()))
