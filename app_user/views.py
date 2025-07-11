from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import redirect, render


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Вы успешно зарегистрировались!")
            return redirect("app_user:login")
    else:
        form = UserCreationForm()
    return render(request, 'app_user/register.html', {'form': form})



def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("app_home:home")
            else:
                form.add_error(None, "Неверное имя пользователя или пароль.")
    else:
        form = AuthenticationForm()
    return render(request, 'app_user/login.html', {'form': form})


def logout_view(request):
    try:
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы.', extra_tags='success')
    except Exception as e:
        messages.error(request, f'Произошла ошибка при выходе из системы: {e}', extra_tags='error')
    return redirect('app_home:home')

