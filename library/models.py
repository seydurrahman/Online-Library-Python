from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.db.models import Avg

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, related_name="books", on_delete=models.SET_NULL, null=True, blank=True
    )
    cover = models.ImageField(upload_to="covers/", blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} — {self.author}"

    def get_absolute_url(self):
        return reverse("library:book_detail", args=[str(self.id)])

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(avg=Avg("rating"))
        return round(agg["avg"] or 0, 2)

    @property
    def reviews_count(self):
        return self.reviews.count()


class Review(models.Model):
    book = models.ForeignKey(Book, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("book", "user")  # optional: one review per user/book

    def __str__(self):
        return f"Review by {self.user} on {self.book} — {self.rating}"


class Shelf(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Shelves"

    def __str__(self):
        return self.name


class Rack(models.Model):
    shelf = models.ForeignKey(Shelf, related_name="racks", on_delete=models.CASCADE)
    rack_number = models.CharField(max_length=50)
    side_name = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("shelf", "rack_number")
        ordering = ["rack_number"]

    def __str__(self):
        return f"{self.shelf.name} - {self.rack_number}"


class Serial(models.Model):
    rack = models.ForeignKey(Rack, related_name="serials", on_delete=models.CASCADE)
    serial_number = models.CharField(max_length=50)

    class Meta:
        unique_together = ("rack", "serial_number")

    def __str__(self):
        return f"{self.rack} / {self.serial_number}"
