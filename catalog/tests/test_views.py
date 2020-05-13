from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from catalog.models import Author, Genre, Language, Book, BookInstance
import datetime


class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        numbers_of_authors = 13
        for author_num in range(numbers_of_authors):
            Author.objects.create(first_name='Author#%s' % author_num, last_name='Surname#%s' % author_num)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/authors/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

        self.assertTemplateUsed(resp, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] is True)
        self.assertTrue(len(resp.context['author_list']) == 10)

    def test_list_all_authors(self):
        resp = self.client.get(reverse('authors')+'?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] is True)
        self.assertTrue(len(resp.context['author_list']) == 3)


class LoanedBookInstanceByUserListViewTest(TestCase):
    def setUp(self):
        # create users
        test_user_1 = User.objects.create_user(username='Test User 1', password='password')
        test_user_1.save()
        test_user_2 = User.objects.create_user(username='Test User 2', password='password')
        test_user_2.save()

        # create book
        test_author = Author.objects.create(first_name='Michael', last_name='Hartl')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(title='Ruby on Rails Tutorial',
                                        summary='Test summary',
                                        isbn='ABCDEFG',
                                        author=test_author,
                                        language=test_language)
        # create genre as post-step
        Genre.objects.create(name='Tutorial')
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # create 30 bookinstances
        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date = timezone.now() + datetime.timedelta(days=book_copy % 5)
            if book_copy % 2:
                the_borrower = test_user_1
            else:
                the_borrower = test_user_2
            status ='m'
            BookInstance.objects.create(book=test_book,
                                        imprint='Test imprint, 2020',
                                        due_back=return_date,
                                        borrower=the_borrower,
                                        status=status)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/my-books/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='Test User 1', password='password')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'Test User 1')  # check login
        self.assertEqual(resp.status_code, 200)  # check status code
        self.assertTemplateUsed(resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        self.client.login(username='Test User 1', password='password')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        get_ten_books = BookInstance.objects.all()[:10]
        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()

        self.assertTrue('bookinstance_list' in resp.context)

        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], bookitem.borrower)
            self.assertEqual('o', bookitem.status)

    def test_pages_ordered_by_due_date(self):  # pointless
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        self.client.login(username='Test User 1', password='password')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = 0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)

class RenewBookInstanceViewTest(TestCase):

    def setUp(self):
        # create users
        test_user_1 = User.objects.create_user(username='Test User 1', password='password')
        test_user_1.save()

        test_user_2 = User.objects.create_user(username='Test User 2', password='password')
        test_user_2.save()
        permission = Permission.objects.get(name='Set book as returned')
        test_user_2.user_permissions.add(permission)
        test_user_2.save()

        # create book
        test_author = Author.objects.create(first_name='Michael', last_name='Hartl')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(title='Ruby on Rails Tutorial',
                                        summary='Test summary',
                                        isbn='ABCDEFG',
                                        author=test_author,
                                        language=test_language)
        # create genre as post-step
        Genre.objects.create(name='Tutorial')
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # create BookInstance for test user 1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance_1 = BookInstance.objects.create(book=test_book,
                                                               imprint='Unlikely Imprint, 2020',
                                                               due_back=return_date,
                                                               borrower=test_user_1,
                                                               status='o')

        # create BookInstance for test user 2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance_2 = BookInstance.objects.create(book=test_book,
                                                               imprint='Unlikely Imprint, 2020',
                                                               due_back=return_date,
                                                               borrower=test_user_2,
                                                               status='o')

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}))
        # Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        self.client.login(username='Test User 1', password='password')
        resp = self.client.get(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}))
        # Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_logged_in_with_permission_borrowed_book(self):
        self.client.login(username='Test User 2', password='password')
        resp = self.client.get(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_2.pk}))
        # Check that it lets us login - this is our book and we have the right permissions.
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        self.client.login(username='Test User 2', password='password')
        resp = self.client.get(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}))
        # Check that it lets us login. We're a librarian, so we can view any users book
        self.assertEqual(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        self.client.login(username='Test User 2', password='password')
        resp = self.client.get(reverse('book-renew-librarian', kwargs={'pk': '1e511e51-1e51-1e51-1e51-1e511e511e51'}))
        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
        self.client.login(username='Test User 2', password='password')
        resp = self.client.get(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}))
        self.assertEqual( resp.status_code, 200)
        # Check we used correct template
        self.assertTemplateUsed(resp, 'catalog/book_renew_librarian.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        self.client.login(username='Test User 2', password='password')
        resp = self.client.get(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}))
        self.assertEqual(resp.status_code, 200)
        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(resp.context['form'].initial['renewal_date'], date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        self.client.login(username='Test User 2', password='password')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        resp = self.client.post(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}),
                                {'renewal_date': valid_date_in_future})
        self.assertRedirects(resp, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_past(self):
        self.client.login(username='Test User 2', password='password')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        resp = self.client.post(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}),
                                {'renewal_date': date_in_past})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        self.client.login(username='Test User 2', password='password')
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        resp = self.client.post(reverse('book-renew-librarian', kwargs={'pk': self.test_bookinstance_1.pk}),
                                {'renewal_date': invalid_date_in_future})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')


class AuthorCreateViewTest(TestCase):

    def setUp(self):
        # Create a user
        test_user_1 = User.objects.create_user(username='Test User 1', password='password')
        test_user_2 = User.objects.create_user(username='Test User 2', password='password')
        test_user_1.save()
        test_user_2.save()

        permission = Permission.objects.get(name='Can add author')
        test_user_2.user_permissions.add(permission)
        test_user_2.save()

        # Create a book
        test_author = Author.objects.create(first_name='John', last_name='Smith')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('author-create'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/authors/create/')

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        self.client.login(username='Test User 1', password='password')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission(self):
        self.client.login(username='Test User 2', password='password')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.client.login(username='Test User 2', password='password')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_form.html')

    def test_form_date_of_death_initially_set_to_expected_date(self):
        self.client.login(username='Test User 2', password='password')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)

        expected_initial_date = datetime.date(2000, 1, 12)
        response_date = response.context['form'].initial['date_of_death']
        response_date = datetime.datetime.strptime(response_date, "%d/%m/%Y").date()
        self.assertEqual(response_date, expected_initial_date)

    def test_redirects_to_detail_view_on_success(self):
        self.client.login(username='Test User 2', password='password')
        response = self.client.post(reverse('author-create'),
                                    {'first_name': 'Christian Name', 'last_name': 'Surname'})
        # Manually check redirect because we don't know what author was created
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/catalog/authors/'))
