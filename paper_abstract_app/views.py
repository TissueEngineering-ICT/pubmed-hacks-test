from django.shortcuts import render, redirect
from . import pubmed_api
from paper_abstract_app.models import Articlemodel,Journal
from django.http import HttpResponse
import csv,urllib
from .models import Journal
import pandas as pd
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

@login_required
def home(request):
    print("home entered")
    return render(request, 'paper_abstract_app/index.html')

@login_required
def abst(request):
    
    if request.POST['keyward']:
        keyward = request.POST['keyward']
    if 'all' in request.POST:
        num = None
    elif request.POST['num']:
        num = request.POST['num']
    if request.POST['min_date']:
        min_date = request.POST['min_date']
    if request.POST['max_date']:
        max_date = request.POST['max_date']

    '''
    ページ番号を取得してくるようにする
    '''

    Articlemodel.objects.all().delete()
    TERM         = keyward
    NUM          = num
    MIN_DATE     = min_date # yyyy/mm/dd
    MAX_DATE     = max_date # yyyy/mm/dd
   
    AbstractModel_list = pubmed_api.getArticle(TERM,MIN_DATE,MAX_DATE,1)
    Articlemodel.objects.bulk_create(AbstractModel_list)
    AbstractModel = {'Articles':Articlemodel.objects.all()} 
    return render(request, 'paper_abstract_app/abst.html',AbstractModel)

@login_required
def your_view_function(request):

    Articlemodel.objects.all().delete()
    if request.method == 'POST':
        TERM = request.POST.get('keyward')
        MIN_DATE = request.POST.get('min_date')
        MAX_DATE = request.POST.get('max_date')
        total_article_count = pubmed_api.get_article_count(TERM, MIN_DATE, MAX_DATE)
        total_pages = pubmed_api.calculate_pages(total_article_count)
        request.session['TERM'] = TERM
        request.session['MIN_DATE'] = MIN_DATE
        request.session['MAX_DATE'] = MAX_DATE
        request.session['total_pages'] = total_pages
    else:
        total_pages = request.session.get('total_pages')
        TERM = request.session.get('TERM')
        MIN_DATE = request.session.get('MIN_DATE')
        MAX_DATE = request.session.get('MAX_DATE')

    page = int(request.GET.get('page', 1))
    articles = pubmed_api.getArticle(TERM, MIN_DATE, MAX_DATE, page=page, items_per_page=10)
    Articlemodel.objects.bulk_create(articles)

    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return render(request, 'paper_abstract_app/abst.html', {
        'Articles': Articlemodel.objects.all(),
        'next_page': next_page,
        'prev_page': prev_page,
        'current_page': page,
        'total_pages': total_pages
    })


@login_required
def some_view(request):
    articles = Articlemodel.objects.order_by('-journal__impact_factor')
    AbstractModel = {'Articles':articles} 
    return render(request, 'paper_abstract_app/abst.html',AbstractModel)

@login_required
def csv_export(request):

    response = HttpResponse(content_type='text/csv; charset=shift_jis')

    f = "PubMed論文" + "_"  + ".csv"
    filename = urllib.parse.quote((f).encode("shift_jis"))
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'{}'.format(filename)

    writer = csv.writer(response)
    Paper_info_list = Articlemodel.objects.all()
    header = ['PMID','Date_publish','Title','Author','Abstract','JournalTitle','SJR','DOI']
    writer.writerow(header)

    for Paper in Paper_info_list:
        try:
            row = [Paper.PMID, Paper.Date_publish, Paper.Title, Paper.Author, Paper.Abstract, Paper.journal.name, Paper.journal.impact_factor, Paper.DOI]
            writer.writerow([str(item).encode("shift_jis", errors='ignore').decode("shift_jis") for item in row])
        except:
            pass
    return response

def import_impact_factors(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file'] 
        df = pd.read_csv(csv_file)
        for index, row in df.iterrows():
            journal_name = row['Title']  
            impact_factor_str = str(row['SJR']) 
            impact_factor_str = impact_factor_str.replace(',', '')  

            impact_factor = 0.0  # Set default value
            if impact_factor_str:  # Check if the string is not empty
                try:
                    impact_factor = float(impact_factor_str)
                except ValueError:
                    pass  

            journal, created = Journal.objects.get_or_create(
                name=journal_name,
                defaults={'impact_factor': impact_factor},
            )
            if not created:
                journal.impact_factor = impact_factor
                journal.save()

        return render(request, 'import_success.html')
    else:
        return render(request, 'import_form.html')

