from django.shortcuts import render


def index(request):
    context = {}

    return render(request, 'uchicago-cs/index.html', context)
