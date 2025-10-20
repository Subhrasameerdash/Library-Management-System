from __future__ import annotations

import random
from datetime import timedelta, timezone as dt_timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from accounts.models import MemberProfile, User
from catalog.models import Book, BookCopy, Category
from circulation.models import Fine, Loan, Reservation


DEFAULT_PASSWORD = "password123"


class Command(BaseCommand):
    help = "Populate the database with synthetic library data."

    def add_arguments(self, parser):
        parser.add_argument("--books", type=int, default=1000, help="Target number of books.")
        parser.add_argument("--loans", type=int, default=1000, help="Target number of loans.")
        parser.add_argument("--members", type=int, default=600, help="Target number of member accounts.")
        parser.add_argument("--librarians", type=int, default=25, help="Target number of librarian accounts.")
        parser.add_argument("--seed", type=int, default=2025, help="Random seed for reproducibility.")

    def handle(self, *args, **options):
        faker = Faker()
        faker.seed_instance(options["seed"])

        with transaction.atomic():
            categories = self._ensure_categories(faker)
            self.stdout.write(f"Categories available: {len(categories)}")

            books_created = self._ensure_books(faker, categories, options["books"])
            self.stdout.write(f"Books created: {books_created}")

            members_created = self._ensure_members(faker, categories, options["members"])
            self.stdout.write(f"Member accounts ensured: {members_created} new")

            staff_users, staff_created = self._ensure_staff(faker, options["librarians"])
            self.stdout.write(f"Staff accounts ensured: {len(staff_users)} total ({staff_created} new)")

            loans_made, reservations_made, fines_created = self._ensure_loans(
                faker,
                options["loans"],
            )
            self.stdout.write(
                f"Loans created: {loans_made} | Reservations created: {reservations_made} | Fines created: {fines_created}"
            )

        self.stdout.write(self.style.SUCCESS("Library data seeding complete."))

    def _ensure_categories(self, faker: Faker) -> list[Category]:
        names = [
            "Science Fiction",
            "Mystery",
            "Romance",
            "Biography",
            "History",
            "Technology",
            "Education",
            "Children",
            "Health",
            "Travel",
            "Self-Help",
            "Poetry",
            "Philosophy",
            "Business",
            "Art",
            "Cooking",
            "Sports",
            "Law",
            "Mathematics",
            "Fantasy",
        ]
        categories: list[Category] = []
        for name in names:
            category, _ = Category.objects.get_or_create(name=name, defaults={"description": faker.text(max_nb_chars=160)})
            categories.append(category)
        return categories

    def _ensure_books(self, faker: Faker, categories: list[Category], target: int) -> int:
        existing = Book.objects.count()
        needed = max(target - existing, 0)
        created = 0
        if needed == 0:
            return created

        base_number = 9780000000000 + existing
        languages = ["English", "Spanish", "French", "German", "Hindi", "Mandarin"]
        for index in range(needed):
            isbn = f"{base_number + index:013d}"
            category = random.choice(categories)
            book = Book.objects.create(
                title=faker.sentence(nb_words=4).rstrip("."),
                author=faker.name(),
                isbn=isbn,
                category=category,
                publication_date=faker.date_between(start_date="-30y", end_date="today"),
                publisher=faker.company(),
                description=faker.paragraph(nb_sentences=3),
                language=random.choice(languages),
                tags=faker.words(nb=3),
            )
            copy_count = random.randint(2, 4)
            for copy_index in range(copy_count):
                barcode = self._generate_barcode(book.pk, copy_index)
                BookCopy.objects.create(
                    book=book,
                    barcode=barcode,
                    location=f"Shelf {random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}" + str(random.randint(1, 20)),
                )
            created += 1
        return created

    def _generate_barcode(self, book_pk: int, copy_index: int) -> str:
        while True:
            barcode = f"BC{book_pk:05d}{copy_index:02d}{random.randint(0, 999):03d}"
            if not BookCopy.objects.filter(barcode=barcode).exists():
                return barcode

    def _ensure_members(self, faker: Faker, categories: list[Category], target: int) -> int:
        members = list(User.objects.filter(role=User.Role.MEMBER))
        current_count = len(members)
        needed = max(target - current_count, 0)
        created_count = 0
        for offset in range(needed):
            username = f"member{current_count + offset + 1:04d}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password=DEFAULT_PASSWORD,
                role=User.Role.MEMBER,
                first_name=faker.first_name(),
                last_name=faker.last_name(),
            )
            created_count += 1
            profile = getattr(user, "profile", None) or MemberProfile.objects.create(user=user)
            preferred = random.sample(categories, k=random.randint(1, min(5, len(categories))))
            profile.preferred_categories.set(preferred)
        return created_count

    def _ensure_staff(self, faker: Faker, target_librarians: int) -> tuple[list[User], int]:
        staff_users = list(User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN]))
        created_count = 0
        if not User.objects.filter(is_superuser=True).exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password=DEFAULT_PASSWORD,
                role=User.Role.ADMIN,
            )
            staff_users.append(admin)
            created_count += 1
        librarians = [user for user in staff_users if user.role == User.Role.LIBRARIAN]
        additional_needed = max(target_librarians - len(librarians), 0)
        for offset in range(additional_needed):
            username = f"librarian{len(librarians) + offset + 1:03d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "role": User.Role.LIBRARIAN,
                    "is_staff": True,
                    "first_name": faker.first_name(),
                    "last_name": faker.last_name(),
                },
            )
            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                librarians.append(user)
                created_count += 1
            staff_users.append(user)
        unique_staff = list({user.pk: user for user in staff_users}.values())
        return unique_staff, created_count

    def _ensure_loans(self, faker: Faker, target_loans: int) -> tuple[int, int, int]:
        loans_existing = Loan.objects.count()
        needed = max(target_loans - loans_existing, 0)
        if needed == 0:
            return 0, 0, 0

        members = list(User.objects.filter(role=User.Role.MEMBER))
        staff = list(User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN]))
        available_copies = list(BookCopy.objects.filter(status=BookCopy.Status.AVAILABLE))
        loans_created = 0
        reservations_created = 0
        fines_created = 0

        for _ in range(needed):
            if not available_copies or not members:
                break
            copy = random.choice(available_copies)
            borrower = random.choice(members)
            issued_by = random.choice(staff) if staff else None
            issued_at = faker.date_time_between(start_date="-365d", end_date="-1d", tzinfo=dt_timezone.utc)
            due_window = random.randint(7, 28)
            due_at = issued_at + timedelta(days=due_window)
            loan = Loan(
                copy=copy,
                borrower=borrower,
                issued_by=issued_by,
                issued_at=issued_at,
                due_at=due_at,
                notes=faker.sentence(nb_words=6),
            )
            loan.save()
            loans_created += 1

            if random.random() < 0.6:
                return_gap = random.randint(1, 40)
                return_at = issued_at + timedelta(days=return_gap)
                if return_at > timezone.now():
                    return_at = timezone.now() - timedelta(days=random.randint(1, 5))
                loan.mark_returned(return_time=return_at)
            else:
                available_copies.remove(copy)
                overdue_days = (timezone.now() - loan.due_at).days
                if overdue_days > 3:
                    amount = Decimal(random.randint(5, 40))
                    fine = Fine.objects.create(member=borrower, loan=loan, amount=amount)
                    if random.random() < 0.5:
                        fine.mark_paid()
                    fines_created += 1

            if random.random() < 0.3:
                book = copy.book
                member = random.choice(members)
                if not Reservation.objects.filter(book=book, member=member, status=Reservation.Status.PENDING).exists():
                    Reservation.objects.create(
                        book=book,
                        member=member,
                        status=Reservation.Status.PENDING,
                        notes=faker.sentence(nb_words=8),
                    )
                    reservations_created += 1

        return loans_created, reservations_created, fines_created
