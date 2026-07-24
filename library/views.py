from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import JsonResponse
from .models import Book, Category, Shelf, Rack, Serial
from .forms import CategoryForm, UserRegisterForm, ReviewForm, BookForm, SelfRackForm
from django.contrib import messages
from django.core.paginator import Paginator


def book_list(request):
    # Browse list with optional search and category filter
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "").strip()

    books = Book.objects.all().select_related("category")

    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q))
    if cat:
        books = books.filter(category__id=cat)
    paginator = Paginator(books, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    context = {
        "books": books,
        "categories": categories,
        "q": q,
        "selected_cat": cat,
        "page_obj": page_obj,
    }
    return render(request, "library/book_list.html", context)


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.select_related("user")

    # handle review post
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to post a review.")
            return redirect("login")
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

    context = {"book": book, "reviews": reviews, "form": form}
    return render(request, "library/book_detail.html", context)


def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. You are logged in.")
            return redirect("library:book_list")
    else:
        form = UserRegisterForm()
    return render(request, "library/register.html", {"form": form})


# Admin-only: check if user.is_staff (or is_superuser)
def staff_check(user):
    return user.is_active and user.is_staff


@user_passes_test(staff_check)
def add_book(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, "Book added.")
            return redirect(book.get_absolute_url())
    else:
        form = BookForm()
    # provide querysets for the form's ModelChoiceFields
    form.fields["shelf"].queryset = Shelf.objects.all()
    if "rack" in form.fields:
        form.fields["rack"].queryset = Rack.objects.all()
    if "serial" in form.fields:
        form.fields["serial"].queryset = Serial.objects.all()
    return render(request, "library/add_book.html", {"form": form})


def load_racks(request):
    """AJAX view to return racks for a given shelf id."""
    shelf_id = request.GET.get("shelf_id")
    racks = []
    if shelf_id:
        racks = list(Rack.objects.filter(shelf_id=shelf_id).values("id", "rack_number"))
    return JsonResponse(racks, safe=False)


def load_serials(request):
    """AJAX view to return serials for a given rack id."""
    rack_id = request.GET.get("rack_id")
    serials = []
    if rack_id:
        serials = list(
            Serial.objects.filter(rack_id=rack_id).values("id", "serial_number")
        )
    return JsonResponse(serials, safe=False)


def category_list(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, "Category added.")
            return redirect("library:category_list")
    else:
        form = CategoryForm()

    categories = Category.objects.all()
    return render(
        request, "library/category_list.html", {"form": form, "categories": categories}
    )


def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("library:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(
        request, "library/category_edit.html", {"form": form, "category": category}
    )


@user_passes_test(staff_check)
def rack_edit(request, pk):
    rack = get_object_or_404(Rack, pk=pk)
    from .forms import RackForm

    if request.method == "POST":
        form = RackForm(request.POST, instance=rack)
        if form.is_valid():
            rack = form.save()
            # update serials: replace with provided list
            serials_text = form.cleaned_data.get("serials", "") or ""
            parts = [
                p.strip()
                for p in serials_text.replace("\n", ",").split(",")
                if p.strip()
            ]
            # create new serials and collect keep ids
            keep = []
            for part in parts:
                s, created = Serial.objects.get_or_create(rack=rack, serial_number=part)
                keep.append(s.id)
            # delete serials not in keep
            rack.serials.exclude(id__in=keep).delete()
            messages.success(request, "Rack updated.")
            return redirect("library:self_rack_add")
    else:
        # prepare initial serials as CSV
        serials_qs = rack.serials.all().values_list("serial_number", flat=True)
        initial_serials = ",".join(serials_qs)
        form = RackForm(instance=rack, initial={"serials": initial_serials})

    return render(request, "library/rack_edit.html", {"form": form, "rack": rack})


@user_passes_test(staff_check)
def self_rack_add(request):
    if request.method == "POST":
        form = SelfRackForm(request.POST)
        if form.is_valid():
            sname = form.cleaned_data["self_name"].strip()
            rnum = form.cleaned_data["rack_number"].strip()
            snum = form.cleaned_data.get("serial_number", "").strip()
            side = form.cleaned_data.get("side_name", "").strip()

            shelf, created_shelf = Shelf.objects.get_or_create(name=sname)
            rack, created_rack = Rack.objects.get_or_create(
                shelf=shelf, rack_number=rnum
            )
            # update side_name if provided
            if side:
                rack.side_name = side
                rack.save()

            created_serial = False
            if snum:
                # allow multiple serials entered as comma-separated values (e.g. "1,2")
                parts = [
                    p.strip() for p in snum.replace("\n", ",").split(",") if p.strip()
                ]
                for part in parts:
                    serial_obj, created = Serial.objects.get_or_create(
                        rack=rack, serial_number=part
                    )
                    created_serial = created_serial or created

            messages.success(request, "Self & Rack added.")
            return redirect("library:self_rack_add")
    else:
        form = SelfRackForm()
    shelves = Shelf.objects.all().prefetch_related("racks__serials")
    return render(
        request,
        "library/self_rack_add.html",
        {
            "form": form,
            "shelves": shelves,
        },
    )
