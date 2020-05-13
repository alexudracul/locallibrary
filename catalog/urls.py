from django.urls import path
from . import views
from django.conf.urls import url

urlpatterns = [
    path('', views.index, name='index'),
    url(r'^books/$', views.BookListView.as_view(), name='books'),
    url(r'^books/(?P<pk>\d+)$', views.BookDetailView.as_view(), name='book-detail'),
    url(r'^authors/$', views.AuthorListView.as_view(), name='authors'),
    url(r'^authors/(?P<pk>\d+)$', views.AuthorDetailView.as_view(), name='author-detail'),
]

# Borrow books
urlpatterns += [
    url(r'^my-books/$', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),
    url(r'^all-borrowed/$', views.AllLoanedBooksListView.as_view(), name='all-borrowed'),
    url(r'^book/(?P<pk>[-\w]+)/renew/$', views.book_renew_librarian, name='book-renew-librarian'),
]

# CRUD authors
urlpatterns += [
    url(r'^authors/create/$', views.AuthorCreate.as_view(), name='author-create'),
    url(r'^authors/(?P<pk>\d+)/update/$', views.AuthorUpdate.as_view(), name='author-update'),
    url(r'^authors/(?P<pk>\d+)/delete/$', views.AuthorDelete.as_view(), name='author-delete'),
]

# CRUD books
urlpatterns += [
    url(r'^books/create/$', views.BookCreate.as_view(), name='book-create'),
    url(r'^books/(?P<pk>\d+)/update/$', views.BookUpdate.as_view(), name='book-update'),
    url(r'^books/(?P<pk>\d+)/delete/$', views.BookDelete.as_view(), name='book-delete'),
]