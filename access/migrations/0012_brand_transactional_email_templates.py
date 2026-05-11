from django.db import migrations


EMAIL_ACTIONS = {
    "REGISTER": {
        "label": "registro",
        "cta": "Ir a mi cuenta",
        "intro": "Tu cuenta fue creada correctamente.",
        "detail": "Conserva este correo como referencia de alta y continua desde el acceso seguro.",
    },
    "VERIFY_ACCOUNT": {
        "label": "confirmacion de cuenta",
        "cta": "Activar mi cuenta",
        "intro": "Tu cuenta esta casi lista.",
        "detail": "Confirma tu correo para habilitar el acceso a la plataforma.",
    },
    "RESEND_ACTIVATION": {
        "label": "reenviar activacion",
        "cta": "Activar mi cuenta",
        "intro": "Generamos un nuevo enlace de activacion.",
        "detail": "Usa este enlace para terminar la configuracion de tu cuenta.",
    },
    "PASSWORD_RESET": {
        "label": "recuperacion de password",
        "cta": "Restablecer password",
        "intro": "Recibimos una solicitud para recuperar tu password.",
        "detail": "Si no solicitaste el cambio, ignora este mensaje y conserva tu acceso actual.",
    },
    "PASSWORD_CHANGED": {
        "label": "password actualizado",
        "cta": "Revisar seguridad",
        "intro": "Tu password fue actualizado.",
        "detail": "Cerramos sesiones y tokens activos para proteger tu cuenta.",
    },
    "EMAIL_RESET": {
        "label": "cambio de email",
        "cta": "Confirmar cambio",
        "intro": "Recibimos una solicitud para cambiar el email de tu cuenta.",
        "detail": "Confirma esta accion solo si reconoces la solicitud.",
    },
    "EMAIL_CHANGED": {
        "label": "email actualizado",
        "cta": "Ir a mi perfil",
        "intro": "El email de tu cuenta fue actualizado.",
        "detail": "Desde tu perfil puedes revisar los datos de contacto vigentes.",
    },
    "VERIFICATION_CODE": {
        "label": "codigo de verificacion",
        "cta": "Verificar acceso",
        "intro": "Generamos un codigo de verificacion para tu cuenta.",
        "detail": "Usalo solamente dentro del flujo que acabas de iniciar.",
    },
    "NEW_DEVICE_LOGIN": {
        "label": "nuevo dispositivo",
        "cta": "Revisar dispositivos",
        "intro": "Detectamos acceso desde un dispositivo nuevo.",
        "detail": "Si no reconoces esta actividad, cambia tu password y revoca sesiones.",
    },
    "ACCOUNT_BLOCKED": {
        "label": "cuenta bloqueada",
        "cta": "Solicitar ayuda",
        "intro": "Tu cuenta fue bloqueada temporalmente.",
        "detail": "El bloqueo protege tu acceso mientras revisamos actividad inusual.",
    },
    "ORGANIZATION_INVITATION": {
        "label": "invitacion",
        "cta": "Aceptar invitacion",
        "intro": "Tienes una invitacion pendiente.",
        "detail": "Aceptala para unirte al espacio de trabajo correspondiente.",
    },
}


BRANDS = {
    "TECNOTELEC": {
        "CommercialName": "Tecno Telec",
        "LogoUrl": "",
        "PrimaryColor": "#0070DE",
        "SenderEmail": "no-reply@tecnotelec.local",
        "SenderName": "Tecno Telec",
        "BaseDomain": "tecnotelec.local",
        "RedirectBaseUrl": "http://localhost:3000",
        "surface": "#FFFFFF",
        "background": "#F3F6FB",
        "text": "#111827",
        "muted": "#4B5563",
        "accent": "#F5B700",
        "headline": "Seguridad y tecnologia para tu proyecto",
        "voice": "Seguimos el mismo acceso claro y empresarial de Tecno Telec: fondo limpio, azul como accion principal y soporte humano cuando lo necesites.",
    },
    "LEXNOVA": {
        "CommercialName": "LexNova",
        "LogoUrl": "/images/lexnova-logo.svg",
        "PrimaryColor": "#0E2A47",
        "SenderEmail": "no-reply@lexnova.local",
        "SenderName": "LexNova",
        "BaseDomain": "lexnova.local",
        "RedirectBaseUrl": "http://localhost:3001",
        "surface": "#FFFFFF",
        "background": "#F7F4EE",
        "text": "#132238",
        "muted": "#596579",
        "accent": "#C5A572",
        "headline": "Acceso seguro a tu espacio legal",
        "voice": "LexNova mantiene un tono sobrio para la gestion y analisis de casos legales, con acciones claras y trazables.",
    },
    "JOBCRON": {
        "CommercialName": "JobCron",
        "LogoUrl": "",
        "PrimaryColor": "#1B6B68",
        "SenderEmail": "no-reply@jobcron.local",
        "SenderName": "JobCron",
        "BaseDomain": "jobcron.local",
        "RedirectBaseUrl": "http://localhost:3002",
        "surface": "#FFFFFF",
        "background": "#F4F6F8",
        "text": "#121826",
        "muted": "#647083",
        "accent": "#D06F2D",
        "headline": "Operacion segura para tu consola ERP",
        "voice": "JobCron usa mensajes compactos y operativos para que el equipo vuelva rapido al flujo diario.",
    },
    "IMAGRAFITY": {
        "CommercialName": "Imagrafity",
        "LogoUrl": "",
        "PrimaryColor": "#334155",
        "SenderEmail": "no-reply@imagrafity.local",
        "SenderName": "Imagrafity",
        "BaseDomain": "imagrafity.local",
        "RedirectBaseUrl": "",
        "surface": "#FFFFFF",
        "background": "#F8FAFC",
        "text": "#0F172A",
        "muted": "#64748B",
        "accent": "#475569",
        "headline": "Acceso seguro a tu cuenta",
        "voice": "Este mensaje protege el acceso a tu aplicacion y conserva un tono claro para acciones de cuenta.",
    },
}


def build_text(brand, action):
    return (
        "Hola{% if user %} {{ user.email }}{% endif %}.\n\n"
        f"{brand['headline']}.\n"
        f"{action['intro']} {action['detail']}\n\n"
        "Continuar: {{ action_url }}\n\n"
        f"{brand['voice']}\n\n"
        "Si no reconoces esta accion, ignora este correo o contacta soporte."
    )


def build_html(brand, action):
    return f"""
<div style="margin:0;padding:32px 0;background:{brand['background']};font-family:Arial,Helvetica,sans-serif;color:{brand['text']};">
  <table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;">
    <tr>
      <td align="center" style="padding:0 16px;">
        <table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;max-width:620px;border-collapse:collapse;background:{brand['surface']};border:1px solid #DCE3EB;border-radius:8px;overflow:hidden;">
          <tr>
            <td style="padding:26px 28px;background:{brand['PrimaryColor']};color:#FFFFFF;">
              <div style="font-size:13px;font-weight:700;text-transform:uppercase;">{{{{ commercial_name }}}}</div>
              <div style="font-size:25px;line-height:1.25;font-weight:800;margin-top:10px;">{brand['headline']}</div>
            </td>
          </tr>
          <tr>
            <td style="padding:30px 28px;">
              <p style="margin:0 0 12px;font-size:16px;line-height:1.6;">Hola{{% if user %}} {{{{ user.email }}}}{{% endif %}}.</p>
              <p style="margin:0 0 12px;font-size:16px;line-height:1.6;">{action['intro']}</p>
              <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:{brand['muted']};">{action['detail']}</p>
              <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr>
                  <td style="background:{brand['PrimaryColor']};border-radius:8px;">
                    <a href="{{{{ action_url }}}}" style="display:inline-block;padding:13px 18px;color:#FFFFFF;text-decoration:none;font-weight:800;">{action['cta']}</a>
                  </td>
                </tr>
              </table>
              <p style="margin:24px 0 0;font-size:13px;line-height:1.6;color:{brand['muted']};">Si el boton no abre, copia este enlace en tu navegador:<br><span style="color:{brand['PrimaryColor']};">{{{{ action_url }}}}</span></p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 28px;background:{brand['background']};border-top:1px solid #DCE3EB;color:{brand['muted']};font-size:12px;line-height:1.5;">
              {brand['voice']}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</div>
""".strip()


def update_brand_templates(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationEmailSettings = apps.get_model("access", "ApplicationEmailSettings")
    TransactionalEmailTemplates = apps.get_model("access", "TransactionalEmailTemplates")

    for application in Applications.objects.all():
        brand = BRANDS.get(application.Code)
        if brand is None:
            brand = {
                **BRANDS["JOBCRON"],
                "CommercialName": application.Name,
                "SenderName": application.Name,
            }

        ApplicationEmailSettings.objects.update_or_create(
            ApplicationID=application,
            defaults={
                "CommercialName": brand["CommercialName"],
                "LogoUrl": brand["LogoUrl"],
                "PrimaryColor": brand["PrimaryColor"],
                "SenderEmail": brand["SenderEmail"],
                "SenderName": brand["SenderName"],
                "BaseDomain": brand["BaseDomain"],
                "RedirectBaseUrl": brand["RedirectBaseUrl"],
                "IsActive": True,
            },
        )

        for action_code, action in EMAIL_ACTIONS.items():
            TransactionalEmailTemplates.objects.update_or_create(
                ApplicationID=application,
                ActionCode=action_code,
                LanguageCode="es-MX",
                Channel="EMAIL",
                defaults={
                    "SubjectTemplate": f"{brand['CommercialName']} - {action['label']}",
                    "TextBodyTemplate": build_text(brand, action),
                    "HtmlBodyTemplate": build_html(brand, action),
                    "IsActive": True,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0011_seed_transactional_email_templates"),
    ]

    operations = [
        migrations.RunPython(update_brand_templates, migrations.RunPython.noop),
    ]
