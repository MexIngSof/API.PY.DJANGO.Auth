from djoser import email

class ActivationEmail(email.ActivationEmail):
    template_name = 'djoser/email/activation.html'  # 👈 cambia el nombre a algo único

class PasswordResetEmail(email.PasswordResetEmail):
    template_name = 'djoser/email/password_reset.html'
