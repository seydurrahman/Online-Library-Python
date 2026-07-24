from django.contrib import admin
from .models import Category, Book, Review, Shelf, Rack, Serial


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "created_at")
    list_filter = ("category", "author")
    search_fields = ("title", "author")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("book__title", "user__username", "comment")


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ("rack_number", "shelf")
    list_filter = ("shelf",)
    search_fields = ("rack_number",)


@admin.register(Serial)
class SerialAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "rack")
    search_fields = ("serial_number",)
