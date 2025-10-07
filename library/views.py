from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Book, Category
from .forms import UserRegisterForm, ReviewForm, BookForm
from django.contrib import messages
from django.core.paginator import Paginator


def book_list(request):
    # Browse list with optional search and category filter
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '').strip()

    books = Book.objects.all().select_related('category')

    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q))
    if cat:
        books = books.filter(category__id=cat)
    paginator = Paginator(books,6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    context = {'books': books, 'categories': categories, 'q': q, 'selected_cat': cat, "page_obj":page_obj}
    return render(request, 'library/book_list.html', context)

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.select_related('user')

    # handle review post
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to post a review.")
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Prevent duplicate review if unique_together is set — handle gracefully
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            try:
                review.save()
                messages.success(request, "Review posted.")
                return redirect(book.get_absolute_url())
            except Exception as e:
                # e.g. unique_together violation
                messages.error(request, "You have already reviewed this book.")
    else:
        form = ReviewForm()

    context = {'book': book, 'reviews': reviews, 'form': form}
    return render(request, 'library/book_detail.html', context)

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. You are logged in.")
            return redirect('library:book_list')
    else:
        form = UserRegisterForm()
    return render(request, 'library/register.html', {'form': form})

# Admin-only: check if user.is_staff (or is_superuser)
def staff_check(user):
    return user.is_active and user.is_staff

@user_passes_test(staff_check)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, "Book added.")
            return redirect(book.get_absolute_url())
    else:
        form = BookForm()
    return render(request, 'library/add_book.html', {'form': form})
