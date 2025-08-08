from django.shortcuts import render

def login(request):
    return render(request, "login.html")
def forgot_password(request):
    return render(request, 'forgot_password.html')
def dashboard(request):
    return render(request, "dashboard.html")